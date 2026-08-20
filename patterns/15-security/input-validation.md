---
name: Input Validation
slug: input-validation
family: 15-security
category: Security
aliases: [Input Checking, Data Validation, Request Validation, Schema Validation]
first_described: "Common secure programming practice"
maturity: canonical
related: [complete-mediation, fail-securely, secure-by-default, defense-in-depth, sql-injection, output-encoding]
incompatible_with: [client-side-only-validation, denylist-only-filtering, parse-after-trust]
verified: 2026-08-02
---

# Input Validation

## 1. Name, aliases, and lineage

The canonical name is Input Validation. Common aliases are **input checking**,
**data validation**, **request validation**, **schema validation**, **form
validation**, and **parameter validation**. In security taxonomies the matching
failure name is often **Improper Input Validation**. MITRE's CWE-20 entry uses
that title for the weakness where a product receives input or data but does not
validate, or validates wrongly, that the input has the properties needed for
safe and correct processing ([CWE-20](https://cwe.mitre.org/data/definitions/20.html),
verified 2026-08-02).

Input Validation is not a Gang of Four object pattern. It is a security and
correctness pattern with older roots in defensive programming, parser design,
database integrity, protocol conformance, and web application security. OWASP
frames it as a security function that checks that only properly formed data
enters a workflow, and distinguishes syntactic validation from semantic
validation ([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
verified 2026-08-02). JSON Schema gives the same idea a machine-readable shape
for JSON values through validation vocabularies and keywords
([JSON Schema Validation 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation),
verified 2026-08-02).

The name is contested only when teams overload it. Some teams use "validation"
for user interface hints. Some use it for persistence constraints. Some use it
for authorization gates. This entry uses the security meaning: convert raw
untrusted input into typed, normalized, domain-checked data, or reject it before
the rest of the system treats it as trustworthy.

Engineering judgement: the best mental model is a border checkpoint between a
raw world and a typed domain world. The pattern earns its place when code after
the checkpoint can rely on a smaller set of values than the external protocol
can express.

## 2. Problem and context

A program accepts bytes, strings, numbers, objects, headers, files, paths,
identifiers, query parameters, form fields, JSON bodies, environment variables,
messages, or records from outside its own trust boundary. Those values then
drive parsing, routing, allocation, database writes, shell calls, object lookups,
authorization decisions, business rules, and user-visible output. If the program
does not reject or normalize bad values before those operations, invalid data can
spread into downstream code that was written for a narrower contract.

The common code smell is a handler that reads a string and passes it onward as
if it were already a product ID, date, amount, path, enum, locale, email
address, role name, or file type. The first function sees only a string. The
second function assumes a typed value. The gap between those two beliefs is
where input bugs live. CWE-20 lists length, quantity, index, type, syntax,
cross-field consistency, domain rules, equivalence, and authenticity as
properties that may need checking for input data or metadata
([CWE-20](https://cwe.mitre.org/data/definitions/20.html), verified
2026-08-02).

Input Validation fits systems where external data crosses a boundary and then
feeds code that has a narrower domain contract than the wire format. Web APIs,
message consumers, CLIs, plug-in boundaries, batch imports, file upload paths,
configuration loaders, and internal service calls all fit that context. OWASP
says data from all untrusted sources should be subject to validation, including
external partners and backend feeds, not only browser clients
([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
verified 2026-08-02).

The context has three parts.

- A boundary exists where raw input can be collected before use.
- The program can state the allowed syntax and the domain rules with enough
  precision to reject bad values.
- The caller can receive a refusal that is clear enough for correction but not
  rich enough to reveal sensitive internals.

Engineering judgement: validation should live as close as possible to the first
trusted interpretation of data. Too early, and the code validates the wrong
representation. Too late, and invalid values may already have changed state,
spent CPU, allocated memory, or reached a sink.

## 3. Forces

Engineering judgement: this dimension weighs trade-offs. Citations anchor
standard mechanisms, while the force ranking is design reasoning.

- **Latency.** Sacrificed. Validation adds parsing, type conversion, length
  checks, set membership checks, cross-field rules, and sometimes I/O such as
  uniqueness or existence checks. The cost is often small, but it is paid on
  every accepted and rejected request.
- **Coupling.** Favoured when validators sit at the boundary. Domain code stops
  knowing about wire formats and receives typed values. Sacrificed when every
  layer repeats its own variant of the same rule.
- **Consistency.** Favoured. A named schema or validator lets every entry point
  share one contract. Consistency is lost when clients, servers, workers, and
  database constraints each carry different ranges or enum lists.
- **Operability.** Favoured if validation failures are counted by field, rule,
  source, and endpoint. Sacrificed if validation returns one generic error that
  hides which contract was breached.
- **Cost.** Mixed. The pattern adds authoring and maintenance cost for schemas,
  validators, tests, and messages. It lowers incident cost by rejecting invalid
  states before they need cleanup.
- **Team topology.** Favoured when platform teams publish shared validators for
  common identifiers and product teams own domain rules. Sacrificed when a
  central team becomes the only group allowed to update every field rule.
- **Cognitive load.** Favoured for readers of domain code, because types and
  value objects carry meaning. Sacrificed for readers of the boundary, because
  a good validator is often more explicit than the business handler.
- **User experience.** Mixed. Accurate validation gives fast, field-level
  feedback. Over-tight validation blocks legitimate values, especially names,
  addresses, email formats, Unicode text, and partner data.

The pattern favours data integrity, security, and downstream simplicity. It
sacrifices some request time, authoring time, and tolerance for unknown input.

## 4. Applicability and non-applicability

Reach for Input Validation when the following hold.

- Raw input crosses a trust boundary and will be parsed, stored, routed, or sent
  to another component.
- The system can state a contract for the value: type, length, range, format,
  enum membership, object shape, cross-field relation, or domain rule.
- Invalid values can cause state corruption, unexpected control flow, resource
  exhaustion, injection, tenant confusion, or wrong business decisions.
- Several entry points accept the same concept and need the same rule, such as
  account IDs, SKUs, country codes, ISO dates, money amounts, or feature names.
- The program needs a typed representation before business logic runs.
- A protocol or schema already defines the input shape, such as JSON Schema,
  OpenAPI, Protobuf, SQL constraints, or a vendor contract.
- A boundary crosses a language, process, machine, tenant, plug-in, or storage
  trust line.

Do NOT reach for Input Validation in these cases.

- **The value is not input.** A value produced by trusted code in the same
  invariant-preserving module may need assertions or type checks, not boundary
  validation. Revalidating every local variable spreads noise and hides the real
  boundary.
- **The rule is authorization.** "Can this subject read this account" is an
  access-control question. Validate that the account ID is well formed, then ask
  an authorizer whether the subject may use it.
- **The problem is output interpretation.** Input Validation does not replace
  context-aware output encoding for HTML, JavaScript, SQL, LDAP, shell, or XML.
  OWASP states that input validation is not the primary method for preventing
  XSS or SQL injection ([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
  verified 2026-08-02).
- **The rule cannot be known at the boundary.** Some checks need data produced
  later, such as a risk score after fraud analysis. Capture a typed candidate
  value first, then validate the later rule at the later boundary.
- **The user needs free-form content.** Comments, biographies, messages, and
  rich text usually cannot be reduced to a small character set without blocking
  real users. Validate length, encoding, structure, and allowed markup policy,
  then encode or sanitize at output.
- **The field is security-sensitive but intentionally opaque.** Passwords,
  recovery codes, encrypted blobs, and signed tokens should be checked for size,
  encoding, and container shape. Do not impose content rules that reduce entropy
  or break future token formats.
- **The validator would duplicate a stronger lower-layer invariant.** A unique
  database index is the authority for uniqueness under concurrency. Application
  validation can improve the message, but it cannot replace the constraint.
- **The only validation is a denylist of attack strings.** CWE recommends an
  accept-known-good strategy and warns against relying only on malicious-looking
  patterns ([CWE-20](https://cwe.mitre.org/data/definitions/20.html), verified
  2026-08-02). A denylist can be a detection aid, not the primary contract.
- **The check runs only in the client.** Client checks help user feedback, but
  server-side checks are still needed because clients can be changed or skipped;
  both OWASP and CWE make this point for server-side security
  ([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
  verified 2026-08-02; [CWE-20](https://cwe.mitre.org/data/definitions/20.html),
  verified 2026-08-02).

## 5. Structure

The participants are named by their runtime role.

- **Untrusted Source.** The browser, service, CLI user, queue, file, database,
  partner feed, environment, or plug-in that provides raw data.
- **Boundary Adapter.** The controller, route handler, consumer, parser, upload
  handler, command loader, or RPC method that receives raw values and has enough
  request context to choose a validator.
- **Canonicalizer.** The component that decodes and normalizes the input into
  one internal representation before rules run. CWE warns that inputs should be
  decoded and canonicalized before validation, and that double decoding can
  bypass schemes ([CWE-20](https://cwe.mitre.org/data/definitions/20.html),
  verified 2026-08-02).
- **Syntactic Validator.** The rule set for shape: type, required fields,
  length, allowed characters, enum membership, numeric range, date format, JSON
  schema, and object structure.
- **Semantic Validator.** The rule set for meaning in the business context:
  start before end, amount within product limits, country allowed for the
  merchant, SKU active for the tenant, or parent and child identifiers matching.
  OWASP names syntactic and semantic validation as separate levels
  ([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
  verified 2026-08-02).
- **Violation Reporter.** The mapper from rule failure to safe error response,
  log event, metric label, and developer-readable diagnostic.
- **Validated Value.** The typed, normalized value object or data transfer object
  that downstream code may use without consulting the raw input again.
- **Domain Consumer.** The application service, repository, workflow, or command
  handler that accepts only the validated value.

Relationships. The Boundary Adapter receives raw input from the Untrusted
Source. It passes the raw value through the Canonicalizer, then through
syntactic and semantic validators. The Violation Reporter handles failures. On
success, the Boundary Adapter constructs a Validated Value and passes that value
to the Domain Consumer. The Domain Consumer never reaches back to raw request
data.

## 6. ASCII structure diagram

```
  +------------------+       raw        +----------------------+
  | Untrusted Source | ---------------> |   Boundary Adapter   |
  +------------------+                  +----------+-----------+
                                                    |
                                                    v
                                         +----------+-----------+
                                         |    Canonicalizer     |
                                         +----------+-----------+
                                                    |
                                                    v
       failure        +------------------+   +------+------+
  +------------------ | Violation        | <-| Syntactic   |
  | error, log,       | Reporter         |   | Validator   |
  | metric            +------------------+   +------+------+
  +--------------------------------------------- | --------+
                                                 v
                                          +------+------+
                                          | Semantic    |
                                          | Validator   |
                                          +------+------+
                                                 |
                                                 v
                                          +------+------+
                                          | Validated   |
                                          | Value       |
                                          +------+------+
                                                 |
                                                 v
                                          +------+------+
                                          | Domain      |
                                          | Consumer    |
                                          +-------------+

  Raw input is used only left of the Validated Value boundary.
```

## 7. Dynamics

The runtime flow is a gate. A request either produces a typed value or stops
with a refusal. The important dynamic rule is that domain code is never called
with raw input.

```
Source        Adapter       Canonicalizer   Syn Rules   Sem Rules   Domain
  |              |               |              |           |          |
  |-- request -->|               |              |           |          |
  |              |-- decode ---->|              |           |          |
  |              |<-- value -----|              |           |          |
  |              |-- check ------------------->|           |          |
  |              |<-- ok or violations --------|           |          |
  |              |-- check -------------------------------->|          |
  |              |<-- ok or violations ---------------------|          |
  |              |                                                  |
  |              |-- if ok, build ValidatedValue ------------------>|
  |              |<-- result ---------------------------------------|
  |<-- success --|                                                  |
  |              |                                                  |
  |<-- 4xx error |  on validation failure, Domain is not called      |
  |              |                                                  |
```

Two ordering rules matter. First, decode and normalize before validation, then
avoid decoding the same value later. CWE links decode-before-validate and
double-decode mistakes to validation bypasses ([CWE-20](https://cwe.mitre.org/data/definitions/20.html),
verified 2026-08-02). Second, run semantic checks after syntactic checks, since
semantic rules should not reason over missing, untyped, or malformed fields.

Engineering judgement: the best implementation makes the dynamics visible in
types. A function that accepts `RawRequest` can parse. A function that accepts
`CreateTransferCommand` should not parse again. If a domain function still reads
`req.body`, the boundary is leaking.

## 8. Implementation variants

**Handwritten validators.** A small function checks one value or one command and
returns either a typed value or a list of violations. This is the clearest form
for domain rules that do not match a generic schema language. The cost is drift
when similar rules are copied between endpoints.

**Schema-first validation.** A JSON Schema, OpenAPI schema, XML Schema, Protobuf
descriptor, or similar contract drives runtime checks. JSON Schema 2020-12
defines validation vocabulary keywords for structural validation of JSON data
([JSON Schema Validation 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation),
verified 2026-08-02). This variant works well at API boundaries and for
generated clients. It is weaker for cross-record and business-state checks.

**Type-constructor validation.** A value object constructor accepts raw data,
checks it, and returns a type that cannot represent invalid states. Examples are
`EmailAddress`, `PositiveMoney`, `Sku`, `TenantId`, or `DateRange`. This variant
shrinks downstream checks. The cost is more small types and conversion code.

**Framework form or model validation.** Web frameworks attach validators to
fields and models. Django forms run `to_python()`, `validate()`,
`run_validators()`, field-specific cleaning, and form-level cleaning in a
defined process ([Django form and field validation](https://docs.djangoproject.com/en/5.2/ref/forms/validation/),
verified 2026-08-02). Rails Active Record validations check model objects
before database save and include built-in helpers for common cases
([Rails Active Record Validations](https://guides.rubyonrails.org/active_record_validations.html),
verified 2026-08-02). This variant is productive when the framework owns the
boundary. It can hide rules when business workflows also accept data outside
forms or models.

**Parser as recognizer.** The parser accepts only the language the program
supports and produces an abstract syntax tree or typed command. CWE names
language-theoretic security as a design strategy that treats parsing as a
distinct layer between raw input and internal representations
([CWE-20](https://cwe.mitre.org/data/definitions/20.html), verified
2026-08-02). This variant fits complex formats, file imports, and protocols.
The cost is parser design and careful error recovery.

**Database-backed validation.** Database constraints enforce uniqueness,
foreign keys, check constraints, type ranges, and nullability. This variant is
the authority for invariants under concurrency. It should be paired with
application validation for clear user errors and earlier rejection.

**Policy or admission validation.** Infrastructure control planes validate
resource changes before persistence. Kubernetes admission controllers intercept
requests to the API server before object persistence, after authentication and
authorization, and can validate or mutate modify requests
([Kubernetes admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/),
verified 2026-08-02). This variant fits cluster and platform policy. It cannot
validate read paths in Kubernetes admission, because the cited documentation
states reads bypass that layer.

**Two-phase validation.** The first phase checks shape and cheap local rules.
The second phase checks business state or external systems, such as inventory,
credit limits, or uniqueness. This keeps request rejection fast while still
placing expensive rules before state change.

## 9. Known production uses

**Django forms and validators.** Django documents a validation flow where
`Field.clean()` runs type conversion, field validation, and reusable validators,
then form-specific cleaning runs for single fields and cross-field rules. Django
validators are callables that raise `ValidationError` on invalid input
([Django form and field validation](https://docs.djangoproject.com/en/5.2/ref/forms/validation/),
verified 2026-08-02; [Django validators](https://docs.djangoproject.com/en/5.2/ref/validators/),
verified 2026-08-02).

**Ruby on Rails Active Record validations.** Rails documents model-level
validations that check Active Record objects before saving them to the database,
with helpers for presence, length, numericality, inclusion, uniqueness, custom
validators, and validation contexts
([Rails Active Record Validations](https://guides.rubyonrails.org/active_record_validations.html),
verified 2026-08-02).

**Kubernetes admission control.** Kubernetes admission controllers are compiled
or configured checks in the API server path for resource modification requests.
The documentation states that they check data arriving in create, delete, or
modify requests before resource persistence, and that validating controllers may
not mutate data
([Kubernetes admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/),
verified 2026-08-02).

**Pydantic validators.** Pydantic documents before, after, plain, and wrap
validators for model fields, with validators used to customize validation around
typed Python models
([Pydantic validators](https://pydantic.dev/docs/validation/latest/concepts/validators/),
verified 2026-08-02).

## 10. Consequences

Positive.

- Downstream code receives typed, normalized values instead of raw protocol
  strings.
- Invalid states are rejected before they reach storage, queues, command
  handlers, shell calls, file paths, or allocation-heavy code.
- The same rule can be reused across API, UI, worker, and import paths when the
  validator is a named component.
- Validation failures become a source of security telemetry, especially when a
  client submits values that the official UI could not produce.
- Domain concepts become visible in code through value objects and schemas.
- Tests can target rule contracts directly rather than setting up full request
  flows for every bad value.

Negative.

- Validators become another layer that must evolve when business rules change.
- Over-tight rules reject legitimate input and create support load.
- Under-tight rules create false confidence because the code appears protected.
- Validation can duplicate database constraints, framework checks, client-side
  hints, and partner schemas unless ownership is explicit.
- Large schemas and deeply nested error lists can be hard for users and
  operators to understand.
- Expensive semantic checks can add latency and can create a denial-of-service
  target if unauthenticated callers trigger them at high volume.
- A validator written with a vulnerable regular expression can become the slow
  path attackers target.

Engineering judgement: the biggest cost is rule ownership. The code is often
easy. Keeping every rule aligned with product policy, database constraints,
partner contracts, and error copy is the hard part.

## 11. Failure modes and misuse

Engineering judgement: the failure symptoms below are drawn from production
practice. Cited sources support the underlying categories, not each example.

**Client-side-only validation.** Symptom. The browser blocks a bad value during
normal use, but a crafted HTTP request reaches the server and changes state.
Cause. The server trusted JavaScript validation. Fix. Repeat security-relevant
validation on the server, and treat client validation as feedback only. OWASP
and CWE both warn that client-side checks can be bypassed
([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
verified 2026-08-02; [CWE-20](https://cwe.mitre.org/data/definitions/20.html),
verified 2026-08-02).

**Denylist as contract.** Symptom. Logs show blocked strings such as `<script>`
while a different encoding, casing, nesting, or grammar form still reaches the
sink. Cause. The validator searched for known bad patterns rather than defining
the allowed language. Fix. Define the allowed type, length, syntax, enum, range,
and domain relation; keep denylist rules only as detection or coarse rejection.

**Validate before decode.** Symptom. A path, tag, or identifier passes the first
check, then becomes dangerous after URL decoding, Unicode normalization, archive
expansion, or framework parsing. Cause. Validation ran on a representation that
was not the one the sink consumed. Fix. Canonicalize once before validation and
pass the canonical value downstream.

**Double decoding.** Symptom. A test with one encoded layer is rejected, but a
payload with two encoded layers passes validation and changes meaning later.
Cause. One component decodes and validates, another component decodes again.
Fix. Store the decoded value in a type that cannot be decoded again, and ban
access to the raw string after the boundary.

**Schema covers shape but not meaning.** Symptom. A JSON body passes schema
validation with correct types, yet creates a transfer with `startDate` after
`endDate`, a discount over the tenant limit, or a child object owned by a
different account. Cause. Structural validation was mistaken for domain
validation. Fix. Add semantic validators after schema validation.

**Regular expression denial of service.** Symptom. CPU spikes on requests that
fail validation, often before authentication, and traces point to a regex match.
Cause. A backtracking expression has worst-case behaviour on crafted input.
OWASP warns readers to be aware of ReDoS when designing regular expressions
([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
verified 2026-08-02). Fix. Use simple anchored expressions, length caps before
matching, parser libraries, or a regex engine with bounded execution.

**Normalization damages user data.** Symptom. A user's name, address, title, or
message is stored in a changed form that the user cannot recover. Cause.
Canonicalization rewrote data beyond what the product contract permitted. Fix.
Separate normalization needed for comparison from preservation needed for
display, and store both when the product requires fidelity.

**Validation split across layers.** Symptom. The API accepts a value, the worker
rejects it, the database accepts a third range, and customer support cannot
explain which rule is true. Cause. Rule ownership drifted between UI, API,
worker, and database. Fix. Make one contract authoritative, generate or reuse
validators where feasible, and test every entry point against the same examples.

**Silent coercion.** Symptom. `"0012"` becomes `12`, `"false"` becomes truthy,
empty string becomes zero, or an unknown enum falls back to a default. Cause.
The conversion API had permissive semantics and the validator treated a coerced
value as accepted. Fix. Use strict parsers, reject lossy conversions, and test
ambiguous inputs.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Input Validation | Output Encoding | Parameterized Query | Database Constraint | Authorization Check | Runtime Assertion |
|---|---|---|---|---|---|---|
| Primary boundary | Before trusted interpretation | At output sink | At database query sink | At persistence | Before protected action | Inside trusted code |
| Coupling | Low when validators produce domain values | Low at sink, no domain contract | Low for SQL construction only | Tied to database schema | Tied to policy model | Tied to local code path |
| Consistency | Strong when shared | Does not check input consistency | Does not check business consistency | Strong for persisted data | Strong for access policy | Local only |
| Latency | Paid before use | Paid at render or sink | Paid at query creation | Paid on write | Paid on protected action | Usually tiny |
| Injection defense | Helps reduce bad input, not enough alone | Strong for output contexts | Strong for SQL value binding | Not a query defense | Not a query defense | Not a sink defense |
| Data integrity | Strong before state change | Weak | Weak beyond query syntax | Strong under concurrency | Weak | Medium for programmer mistakes |
| User feedback | Good field-level messages | Late or invisible | Database-like errors unless wrapped | Often late, sometimes generic | Permission messages | Usually not user-facing |
| Team ownership | Product plus platform | UI or sink owners | Data access owners | Database owners | Security or platform owners | Module owners |
| Best fit | Raw external data | Rendering and command sinks | SQL calls | Invariants in storage | Subject action object decisions | Internal invariants |

Reading of the table. Input Validation answers "is this value well formed and
allowed for this operation." Output Encoding answers "how is this value safely
represented in this output context." Parameterized Query answers "how is this
value bound into SQL without becoming SQL syntax." Database Constraint answers
"what state may exist under concurrent writes." Authorization Check answers
"may this subject do this action on this object." Runtime Assertion answers
"did trusted code violate its own invariant."

## 13. Related and incompatible patterns

- **Complete Mediation.** Composes with Input Validation. Validation proves the
  request shape and domain candidate. Complete Mediation decides access on every
  protected operation.
- **Fail Securely.** Composes with it. A validator that cannot parse, cannot
  fetch needed rule data, or cannot classify a value should fail closed for
  security-relevant actions.
- **Secure by Default.** Composes with it. Default rule sets should reject
  unknown fields, unknown enum values, overlong strings, and unsupported object
  variants unless compatibility policy says otherwise.
- **Defense in Depth.** Explains why validation does not stand alone. A system
  still needs output encoding, parameterized queries, database constraints,
  authorization, rate limits, and safe parsers.
- **Output Encoding.** Complements it and often replaces bad validation rules.
  For free-form text, accept characters the product permits, then encode when
  placing the data in HTML, JavaScript, SQL, logs, CSV, or shell contexts.
- **Parameterized Query.** Replaces input filtering as the primary defense for
  SQL injection. Validation can reject impossible IDs or amounts; binding keeps
  values from becoming SQL syntax.
- **Schema Validation.** A variant of Input Validation. It is strong for shape
  and basic value constraints, weaker for checks that need live business state.
- **Parser Combinator or Interpreter.** A stronger variant for complex input
  languages. The parser recognizes the accepted grammar and returns a typed
  structure.
- **Client-side-only-validation.** Incompatible as a security pattern. It can
  improve feedback, but it cannot be the boundary that protects the server.
- **Denylist-only-filtering.** Incompatible. It does not define an allowed
  language and is easy to bypass when encodings or contexts change.
- **Parse-after-trust.** Incompatible. Code that stores or routes raw input
  before parsing has already crossed the boundary the pattern is meant to
  protect.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Named refactorings
from the refactoring family often apply: Extract Function, Extract Class,
Introduce Parameter Object, Replace Primitive with Object, Move Function, and
Consolidate Duplicate Conditional Fragments.

1. Inventory every place raw input enters the feature: routes, queue consumers,
   imports, CLI flags, scheduled jobs, webhooks, files, environment variables,
   and internal RPC.
2. Pick one boundary and one command. Do not start with a global framework
   rewrite.
3. Name the domain value the handler really needs, such as `CreateTransfer`,
   `TenantSlug`, `Sku`, `DateRange`, or `UploadedImage`.
4. Extract parsing and validation into a function that accepts raw input and
   returns either the domain value or structured violations.
5. Canonicalize once inside that function. Return the canonical value, not the
   raw string.
6. Split syntactic rules from semantic rules. Syntactic rules should not query
   live state. Semantic rules may use repositories or policy data.
7. Change the handler signature or first line so all later code uses the
   domain value. Delete later reads from `req.body`, query maps, form maps, or
   raw headers.
8. Add examples for accepted values, rejected malformed values, rejected
   semantically invalid values, and boundary values.
9. Replace copied rules in nearby handlers with the new validator.
10. Add metrics and safe error mapping before expanding the pattern to the next
    boundary.

Removing the pattern when it stops earning its place.

1. Confirm the boundary no longer accepts untrusted or weakly typed input. A
   private function called only with a validated value may not need validation.
2. Keep database constraints, type constructors, and protocol parsers that still
   protect real boundaries.
3. Inline validators that contain only one local assertion and no reuse.
4. Delete duplicate API-layer rules that are generated from an authoritative
   schema, after tests prove the generated path rejects the same examples.
5. Replace over-specific value objects with primitives only when the type no
   longer prevents an invalid state.
6. Keep observability for rejected external data until traffic proves callers
   no longer send the old shape.

Engineering judgement: do not remove validation because it "never fires." First
check whether it never fires because the rule is dead, or because it is quietly
blocking bad traffic every day.

## 15. Testing and verification

Engineering judgement: validation tests should prove the contract, not the
framework. Test your rules at the smallest boundary that still exercises real
parsing and error mapping.

Easier because of the pattern.

- Accepted and rejected examples can be tested without running the full domain
  workflow.
- Boundary values are explicit: empty, one character, max length, max plus one,
  min, min minus one, unknown enum, missing field, extra field, wrong type, and
  bad cross-field relation.
- Downstream tests can use validated value constructors rather than recreating
  raw request maps.
- Fuzz and property tests have a clear oracle: parser returns a value satisfying
  invariants, or returns violations without crashing.

Harder because of the pattern.

- Error messages become part of the user-facing contract and need tests when
  clients depend on codes.
- Semantic validators that consult state need fixture control and race tests.
- Generated schemas need drift tests against handwritten domain rules.
- Unicode, locale, timezone, and numeric precision cases need sample sets from
  the product domain, not only from developer intuition.

Techniques that apply.

- **Example table tests.** Put accepted and rejected values in a table with
  expected error codes. This catches regressions when rules change.
- **Property tests.** Generate strings, numbers, dates, and object shapes. For
  every accepted value, assert the returned domain type satisfies its invariant.
  For every rejected value, assert the validator returns a safe violation rather
  than throwing an internal error.
- **Mutation tests for missing checks.** Remove or weaken one rule and confirm
  tests fail. This is useful for validators with many similar fields.
- **Contract tests across entry points.** Feed the same examples to API, worker,
  import, and CLI boundaries when they accept the same concept.
- **Database race tests.** For uniqueness and foreign keys, prove the database
  constraint rejects conflicting writes even if application validation passes in
  two concurrent requests.
- **Regression tests for known bypasses.** Keep examples for double decoding,
  unknown enum defaults, overlong strings, and prior incident payloads.

Verification in production should include a synthetic request that violates one
safe rule per public boundary and confirms that the response code, error code,
metric, and log event are all present.

## 16. Observability signals

Engineering judgement: validation telemetry should tell operators whether bad
input is accidental, hostile, caused by a client version drift, or caused by a
server contract change.

What to record.

- A counter for validation failures labelled by endpoint or consumer, field,
  rule code, source class, and client version where available.
- A counter for accepted requests labelled by schema version, so failure rates
  can be interpreted against traffic volume.
- A histogram of validation duration, with separate labels for syntactic and
  semantic phases when semantic checks use I/O.
- A counter for unknown fields and unknown enum values. These often reveal old
  clients, new clients hitting old servers, probing, or rollout mismatch.
- A counter for payloads rejected before parsing because of size, content type,
  compression ratio, nesting depth, or file type.
- A sampled log event with safe rule codes and correlation IDs. Do not log raw
  secrets, full tokens, passwords, payment data, or uploaded file bodies.

A healthy instance on a dashboard. Validation failure rates are low and stable
for normal user traffic. A new release changes failure labels only where the
release notes explain a contract change. Unknown fields appear during planned
client rollouts and then fall. Validation latency is a small fraction of total
request latency. Semantic validation errors are dominated by user-correctable
conditions rather than internal lookup failures.

A failing instance. A sharp rise in one rule code after deploy points at a
contract mismatch. A rise in size, nesting, regex, or content-type failures
before authentication may indicate probing or denial-of-service attempts. A
drop to zero validation failures on a busy endpoint can mean the validator was
removed from the path. A rise in semantic lookup time can turn validation into
the slowest part of the request.

## 17. Security and privacy implications

Input Validation closes part of the attack surface but does not close every
sink. OWASP says validation can reduce the effect of malformed input, but it is
not the primary defense for XSS or SQL injection
([OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
verified 2026-08-02). CWE lists possible consequences of improper validation
including denial of service, confidentiality loss, integrity loss, and possible
unauthorized code or command execution
([CWE-20](https://cwe.mitre.org/data/definitions/20.html), verified
2026-08-02).

Security benefits.

- Reduces the set of values that can reach dangerous sinks.
- Stops many malformed or impossible requests before state change.
- Limits resource consumption by rejecting oversize, overdeep, or overcount
  inputs early.
- Turns suspicious values into telemetry rather than letting them disappear into
  downstream exceptions.
- Makes parser boundaries explicit, which lowers the chance of inconsistent
  interpretation between components.

Security risks.

- A validator can be bypassed if it runs before the final decoding or parsing
  step.
- A slow validator can become the denial-of-service target.
- A permissive coercion rule can turn attacker input into an unintended valid
  value.
- An error message can reveal valid identifiers, enum sets, account existence,
  business limits, or parsing internals.
- Validation can create false confidence if teams remove output encoding,
  parameterized queries, authorization, or database constraints.

Privacy implications.

Validation failures often contain raw user input. That input can include names,
addresses, tokens, health data, payment data, or message text. Logs and metrics
should record rule codes, field names, lengths, and coarse source facts instead
of full values. When values are needed for debugging, sample them under a
privacy review, redact sensitive fields, and apply short retention.

Engineering judgement: treat validation logs as security data and user data at
the same time. They are useful exactly because they show what callers tried to
send, and that is why they need tighter access than ordinary application logs.

## Code examples

Three languages are shown because the pattern has different idioms. TypeScript
shows a discriminated result around JSON-like input. Python shows a value object
constructor and structured violations. Go shows an explicit parser returning a
typed command and error codes. Each sample is minimal and runnable without a
framework.

### TypeScript

```typescript
type ValidationError = { field: string; code: string };
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; errors: ValidationError[] };

type CreateUser = {
  email: string;
  age: number;
  role: "reader" | "editor";
};

function validateCreateUser(input: unknown): Result<CreateUser> {
  const errors: ValidationError[] = [];

  if (typeof input !== "object" || input === null || Array.isArray(input)) {
    return { ok: false, errors: [{ field: "$", code: "object_required" }] };
  }

  const body = input as Record<string, unknown>;
  const email = body.email;
  const age = body.age;
  const role = body.role;

  if (typeof email !== "string" || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    errors.push({ field: "email", code: "email_format" });
  }
  if (typeof age !== "number" || !Number.isInteger(age) || age < 13 || age > 130) {
    errors.push({ field: "age", code: "age_range" });
  }
  if (role !== "reader" && role !== "editor") {
    errors.push({ field: "role", code: "role_allowed" });
  }

  if (errors.length > 0) return { ok: false, errors };
  return {
    ok: true,
    value: {
      email: email as string,
      age: age as number,
      role: role as "reader" | "editor",
    },
  };
}

const result = validateCreateUser({ email: "a@example.com", age: 42, role: "editor" });
console.log(result.ok ? result.value.role : result.errors[0].code);
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    field: str
    code: str


@dataclass(frozen=True)
class TransferCommand:
    from_account: str
    to_account: str
    cents: int


def parse_transfer(raw: dict[str, object]) -> tuple[TransferCommand | None, list[ValidationError]]:
    errors: list[ValidationError] = []
    from_account = raw.get("from_account")
    to_account = raw.get("to_account")
    cents = raw.get("cents")

    if not isinstance(from_account, str) or not from_account.startswith("acct_"):
        errors.append(ValidationError("from_account", "account_id"))
    if not isinstance(to_account, str) or not to_account.startswith("acct_"):
        errors.append(ValidationError("to_account", "account_id"))
    if from_account == to_account:
        errors.append(ValidationError("to_account", "different_account"))
    if not isinstance(cents, int) or cents <= 0 or cents > 1_000_000:
        errors.append(ValidationError("cents", "amount_range"))

    if errors:
        return None, errors
    return TransferCommand(from_account, to_account, cents), []


if __name__ == "__main__":
    command, problems = parse_transfer({
        "from_account": "acct_a",
        "to_account": "acct_b",
        "cents": 2500,
    })
    print(command.cents if command else problems[0].code)
```

### Go

```go
package main

import (
	"fmt"
	"regexp"
)

type ValidationError struct {
	Field string
	Code  string
}

type Signup struct {
	Email string
	Plan  string
	Seats int
}

var emailPattern = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)

func ValidateSignup(raw map[string]any) (Signup, []ValidationError) {
	var errors []ValidationError

	email, emailOK := raw["email"].(string)
	plan, planOK := raw["plan"].(string)
	seats, seatsOK := raw["seats"].(int)

	if !emailOK || !emailPattern.MatchString(email) {
		errors = append(errors, ValidationError{"email", "email_format"})
	}
	if !planOK || (plan != "free" && plan != "team") {
		errors = append(errors, ValidationError{"plan", "plan_allowed"})
	}
	if !seatsOK || seats < 1 || seats > 100 {
		errors = append(errors, ValidationError{"seats", "seat_range"})
	}
	if plan == "free" && seats > 1 {
		errors = append(errors, ValidationError{"seats", "free_plan_limit"})
	}
	if len(errors) > 0 {
		return Signup{}, errors
	}
	return Signup{Email: email, Plan: plan, Seats: seats}, nil
}

func main() {
	signup, errors := ValidateSignup(map[string]any{
		"email": "team@example.com",
		"plan":  "team",
		"seats": 3,
	})
	if len(errors) > 0 {
		fmt.Println(errors[0].Code)
		return
	}
	fmt.Println(signup.Plan)
}
```

## 18. References

1. MITRE. *CWE-20: Improper Input Validation*. CWE version 4.20.
   https://cwe.mitre.org/data/definitions/20.html
   Verified 2026-08-02. Source for the weakness name, input properties,
   consequences, accept-known-good mitigation, client-side warning,
   canonicalization warning, and related validation weaknesses.
2. OWASP Foundation. *Input Validation Cheat Sheet*. OWASP Cheat Sheet Series.
   https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
   Verified 2026-08-02. Source for validation goals, untrusted source coverage,
   syntactic and semantic validation, server-side validation, allowlist guidance,
   free-form text notes, and ReDoS warning.
3. JSON Schema organization. *JSON Schema Validation: A Vocabulary for
   Structural Validation of JSON*. Draft 2020-12.
   https://json-schema.org/draft/2020-12/json-schema-validation
   Verified 2026-08-02. Source for schema-first structural validation.
4. Django Software Foundation. *Django 5.2 documentation*, "Form and field
   validation."
   https://docs.djangoproject.com/en/5.2/ref/forms/validation/
   Verified 2026-08-02. Source for Django's form validation flow and cleaning
   hooks.
5. Django Software Foundation. *Django 5.2 documentation*, "Validators."
   https://docs.djangoproject.com/en/5.2/ref/validators/
   Verified 2026-08-02. Source for reusable Django validators.
6. Ruby on Rails project. *Active Record Validations*. Rails Guides.
   https://guides.rubyonrails.org/active_record_validations.html
   Verified 2026-08-02. Source for Rails model-level validations, validation
   helpers, custom validators, and validation contexts.
7. Kubernetes project. *Admission Control in Kubernetes*.
   https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
   Verified 2026-08-02. Source for admission controller placement, validating
   admission behavior, and the limit that reads bypass admission control.
8. Pydantic project. *Validators*. Pydantic documentation.
   https://pydantic.dev/docs/validation/latest/concepts/validators/
   Verified 2026-08-02. Source for Pydantic field validator variants.
