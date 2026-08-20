---
name: Replace Magic Literal
slug: replace-magic-literal
family: 03-refactoring
category: Refactoring
aliases: [Replace Magic Number with Symbolic Constant, Introduce Constant]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-variable, rename-variable, encapsulate-variable, replace-primitive-with-object, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-02
---

# Replace Magic Literal

## 1. Name, aliases, and lineage

The canonical name is **Replace Magic Literal**. Martin Fowler's current
refactoring catalog lists Replace Magic Literal and gives **Replace Magic Number
with Symbolic Constant** as its alias
(https://refactoring.com/catalog/replaceMagicLiteral.html, verified
2026-08-02). The older name appears in Martin Fowler, *Refactoring. Improving
the Design of Existing Code*, 1st edition, Addison-Wesley, 1999, chapter 8,
"Organizing Data," page 204, "Replace Magic Number with Symbolic Constant."
The second edition, Martin Fowler, *Refactoring. Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 6, "A First Set of
Refactorings," broadens the idea from numbers to literals.

The name changed because the smell is not limited to numbers. A source file can
hide meaning in a string, byte, character, date format, regular expression,
HTTP header name, Kubernetes label key, CSS length, environment variable name,
or retry count. The value is magic when the reader must already know the
domain to infer what it means.

The common alias **Introduce Constant** describes the mechanics rather than the
problem. It is a fine local name during code review, but it can be too broad as
a pattern name because not every new constant is a replacement for a magic
literal. Some constants name new public API. Some encode protocol registries.
Some tune internal policy. Replace Magic Literal is narrower. It begins with an
existing literal at one or more call sites and gives that literal an intention
revealing name.

The older phrase **magic number** is still useful when the literal is numeric.
It is also risky because it tempts reviewers to ignore magic strings. In modern
systems, magic strings often create more damage than magic numbers because they
cross process and organization boundaries. A typo in `app.kubernetes.io/name`,
`Content-Type`, `DATABASE_URL`, or `application/json` can break integration
while all local unit tests still pass.

Judgement. Treat "magic" as a reader effect, not as a data type. A literal is
magic when its meaning is carried by memory, convention, or a distant document
rather than by the source line in front of the reader.

## 2. Problem and context

A literal value appears in executable code, configuration assembly, tests, or
queries, and the value has domain meaning that is not visible at the use site.
The code may be correct, but it forces readers to decode the value before they
can reason about behavior.

The situation often starts small. A handler returns `429` when a caller exceeds
a quota. A scheduler waits `30000` before retrying. A parser tests for `"csv"`.
A storage client writes metadata under `"app.kubernetes.io/name"`. The first
change is easy. A second file repeats the same literal. Later, a bug report
arrives because one place uses `30000`, another uses `30`, and a third uses
`"30s"`. All three intend the same timeout. None says so.

The refactoring extracts the literal to a named constant, enum case, value
object, or domain policy object, then replaces the raw literal with the name.
The constant does not make the value more correct. It makes the meaning
addressable. Once the meaning has a name, the team can search for it, test it,
log it, review changes to it, and decide whether it belongs in code,
configuration, or a richer domain type.

The context matters. Replace Magic Literal is not a ban on all literals.
`0`, `1`, `true`, `false`, and `""` can be clear in local arithmetic or guard
clauses. `for (let i = 0; i < items.length; i++)` does not need
`START_INDEX`. `if (children.length === 0)` does not need
`NO_CHILDREN_COUNT`. The refactoring earns its place when the literal names a
domain rule, protocol token, unit conversion, category, limit, or externally
visible contract.

The problem becomes sharper at boundaries. Protocols and APIs often identify
meaning with literal values. HTTP status codes are three digit integers whose
semantics are defined by RFC 9110 section 15
(https://www.rfc-editor.org/rfc/rfc9110.html#section-15, verified
2026-08-02). Kubernetes labels use string keys and values to organize and
select objects (https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/,
verified 2026-08-02). Those literals are not arbitrary. They are names from a
shared contract. Repeating them raw spreads the contract through the codebase
without a single local vocabulary.

A second boundary problem is partial agreement. Two services may both know that
`"active"` is a state, but one may mean "billing is current" and the other may
mean "the user can sign in." If both services import `ACTIVE`, the name hides a
domain split. If both repeat `"active"`, the split is still hidden. The right
move is to name the local concept first, such as `BILLING_STATUS_ACTIVE` and
`ACCOUNT_ACCESS_ACTIVE`, then decide whether a shared state machine exists.
Replace Magic Literal is therefore not a text substitution exercise. It is a
small act of domain modeling.

The same value can also sit at three layers with three names. An HTTP adapter
may use `HTTPStatus.TOO_MANY_REQUESTS`, a domain service may use
`QuotaDecision.Rejected`, and a product analytics event may use
`quota_rejected`. Collapsing those names into one constant would mix protocol,
domain, and analytics ownership. The refactoring should reduce accidental
duplication without erasing useful boundaries.

## 3. Forces

Judgement. The following forces are engineering tradeoffs. The named standards
and libraries cited elsewhere prove that symbolic names are common in real
systems, but the weighting below is based on design reasoning.

- **Readability.** Favoured when the name is better than the value. A reader
  can understand `DEFAULT_RETRY_DELAY_MS` faster than `30000` when the unit and
  role are otherwise absent. Sacrificed when the name repeats the value, for
  example `THIRTY = 30`.
- **Coupling.** Favoured when callers depend on one local vocabulary rather
  than scattered literals. Sacrificed when a public constant leaks an internal
  rule and downstream code starts depending on it.
- **Consistency.** Favoured because the same concept now has one spelling.
  Changing the value means changing one definition or one small set of related
  definitions.
- **Latency.** Usually neutral. A compile time constant, enum case, or module
  constant has no material runtime cost in ordinary application code. A richer
  value object can add allocation or parsing cost if used in hot loops.
- **Operability.** Favoured when logs, metrics, and traces can emit the
  constant name or policy name beside the raw value. Sacrificed if operators
  only see the symbolic name and not the actual value.
- **Cost.** Favoured when duplicate literals disappear and review scope
  shrinks. Sacrificed when a project creates large constant bags that become
  dumping grounds.
- **Team topology.** Favoured when platform teams publish boundary vocabulary,
  such as status codes, header names, label keys, or feature names. Sacrificed
  when every team invents a private constant for the same shared literal.
- **Cognitive load.** Favoured after the reader learns the vocabulary.
  Sacrificed on first contact because the reader may have to jump to the
  definition to see the value.
- **Change risk.** Favoured for policy values that can change. Sacrificed for
  protocol values that must not change, because a central constant can make an
  accidental contract change wider than a local typo would have been.

The pattern favours meaning, consistency, and searchability. It sacrifices a
small amount of directness. That cost is acceptable when the value encodes a
concept and wasteful when the value is self explaining in its local expression.

## 4. Applicability and non-applicability

Reach for Replace Magic Literal when the following hold.

- The same literal appears in multiple places with the same meaning.
- A literal has a unit, such as milliseconds, bytes, cents, pages, retries, or
  percentage points, and the unit is not visible in the variable or parameter
  name.
- A literal is part of an external contract, such as an HTTP status code,
  header name, media type, database enum value, event name, Kubernetes label
  key, command name, or environment variable key.
- A literal represents business policy, such as a fraud threshold, grace
  period, minimum balance, free trial length, quota, or tier boundary.
- A literal appears in tests as expected behavior and should express the rule
  under test rather than a bare value.
- Two values are numerically equal but mean different things. Separate names
  prevent false unification.
- A value must be logged, measured, or audited by a stable conceptual name.
- A future refactoring may move the value to configuration, a registry, or a
  richer domain type.

Do NOT reach for it in the following non-applicability cases.

- **The literal is part of the language idiom.** `0` as a start index, `1` as
  an increment, and `""` as an empty string are often clearer than named
  constants.
- **The name cannot add meaning.** `TWO = 2` is weaker than the literal. Names
  should encode role, unit, or contract, not spell the value in words.
- **The literal appears once and is clear at the call site.** Extraction can
  create a needless hop. Prefer a local variable only when it explains the
  surrounding expression.
- **The value is a sample in a test fixture or documentation example.** Naming
  every sample can hide what the example is demonstrating.
- **The value belongs in configuration, not code.** A per tenant limit, rollout
  percentage, or endpoint URL may need a typed configuration object instead of
  a compile time constant.
- **The value is secret or private.** API keys, salts, tokens, and credentials
  must not become constants. Use the secret store or runtime environment.
- **The literal is generated code.** Regenerated files will overwrite the
  change. Put the name in the generator or leave the generated output alone.
- **The value is a wire value whose raw form is the readable form.** Some SQL
  fragments, regular expressions, and protocol examples are easier to review
  inline when the local context is tight.
- **The constant would become a dumping ground.** `Constants.java`,
  `constants.ts`, or `values.py` with unrelated entries creates a second
  search problem. Put constants near their owning concept.
- **Two equal literals carry different meanings.** Do not merge them into one
  constant because the value matches today. Name each concept separately.
- **The literal is intentionally local calibration.** A benchmark warmup loop
  or test data size may be clearer inline when the number is not a domain rule.
- **The team cannot agree on a stable concept name.** That disagreement is
  information. Extract a local variable first, or model the domain before
  publishing a shared constant.

## 5. Structure

Replace Magic Literal has five participants.

- **Literal occurrence.** The raw value in executable code, test code, query
  text, configuration assembly, or boundary mapping. It may be a number,
  string, character, boolean, byte sequence, date format, regex, or structured
  literal.
- **Named meaning.** The concept represented by the value. This is the real
  participant. The constant is only a carrier for it.
- **Declaration site.** The smallest stable scope that owns the meaning. It can
  be a local constant, module constant, enum, class constant, namespaced object,
  sealed type, value object, or typed configuration field.
- **Use site.** The code that reads, compares, emits, parses, or stores the
  value after the refactoring. A use site should reveal intent without forcing
  the reader to decode the literal.
- **Boundary adapter.** Optional. The code that translates between the named
  meaning and an external raw value, such as an HTTP status integer or a label
  key. The adapter is where parsing, validation, deprecation, and logging often
  belong.

The central relationship is a replacement relationship. The use site no longer
mentions the raw value directly. It refers to the declaration site. The
declaration site carries both the value and the chosen vocabulary.

Scope is the key structural decision. A constant used by one function belongs
near that function. A constant used by one module belongs in that module. A
constant used across a package belongs behind the package API. A constant used
across services may need an explicit schema, enum, or protocol package rather
than a copied source constant.

Good declaration sites answer three questions. Who owns the meaning. Who may
change the value. Who must be told when it changes. A retry delay owned by a
worker module can be private to that module. A metric name owned by the
observability platform may belong in an instrumentation package. A wire value
owned by a public protocol should come from the language runtime, generated
schema, or small adapter that treats the raw value as a contract.

Naming is part of structure. Prefer names that include the noun being governed,
the rule being applied, and the unit when the type does not carry it. For
example, `MAX_PASSWORD_RESET_ATTEMPTS` is stronger than `MAX_ATTEMPTS` inside a
large authentication package. `SESSION_IDLE_TIMEOUT_SECONDS` is stronger than
`TIMEOUT`, because it tells the reader what can time out and how the number is
measured. Names can be shorter inside a small module because the module name
already supplies context.

## 6. ASCII structure diagram

```
Before

  +----------------------+        +----------------------+
  | quota handler        |        | retry worker         |
  |----------------------|        |----------------------|
  | if count > 1000      |        | sleep(30000)         |
  | return 429           |        | attempts < 3         |
  +----------+-----------+        +----------+-----------+
             |                               |
             | raw values carry meaning      | raw values carry meaning
             v                               v
      reader must infer               reader must infer
      status and policy               units and policy

After

  +----------------------+        +----------------------+
  | quota policy         |        | retry policy         |
  |----------------------|        |----------------------|
  | MAX_REQUESTS = 1000  |        | RETRY_DELAY_MS=30000 |
  | TOO_MANY_REQUESTS=429|        | MAX_ATTEMPTS = 3     |
  +----------+-----------+        +----------+-----------+
             |                               |
             v                               v
  +----------------------+        +----------------------+
  | quota handler        |        | retry worker         |
  |----------------------|        |----------------------|
  | if count > MAX_...   |        | sleep(RETRY_...)     |
  | return TOO_MANY_...  |        | attempts < MAX_...   |
  +----------------------+        +----------------------+
```

## 7. Dynamics

The runtime dynamics are simple for a compile time constant and richer for a
boundary adapter. The refactoring itself is a source transformation, but the
runtime flow changes how values are observed and changed.

```
Refactoring flow

  developer
     |
     v
  find literal occurrences
     |
     v
  decide whether same value means same concept
     |
     +-- no --> create separate names or leave local values alone
     |
     v
  choose smallest owning scope
     |
     v
  declare named value
     |
     v
  replace use sites
     |
     v
  run tests and boundary checks

Runtime flow with a boundary value

  request/event/config
          |
          v
  raw literal arrives
          |
          v
  boundary adapter parses or compares
          |
          v
  named meaning used inside domain code
          |
          v
  raw literal emitted only at external boundary
```

Two runtime effects matter. First, the named value creates a single traceable
point for policy. When behavior changes, review can focus on the declaration
and its owners. Second, the boundary adapter gives a place to reject unknown
values, map deprecated spellings, and attach telemetry. Without that adapter,
raw comparisons tend to spread and each site invents its own fallback.

## 8. Implementation variants

**Local constant.** The smallest variant. Use it when one function contains a
literal that needs a name for readability. It keeps the name near the code and
does not publish API. This is often the best first step before deciding whether
the concept deserves wider scope.

**Module or package constant.** Use it when the same concept appears across a
file or package. This works well for internal policy, internal event names, and
units. The cost is a public search surface. Keep the declaration close to the
owning module rather than adding a global constant file.

**Enum or union type.** Use it when the value comes from a closed set. Python's
`HTTPStatus` is an enum that names IANA registered HTTP status codes and keeps
the integer value available (https://docs.python.org/3/library/http.html,
verified 2026-08-02). TypeScript string unions, Rust enums, Java enums, and
Swift enums serve the same role when raw strings or integers have known cases.

**Typed value object.** Use it when a literal has validation, unit conversion,
or behavior. Money, duration, percentage, distance, email address, and media
type often deserve value objects. The cost is more code and possible allocation.
Judgement. Move from constant to value object when operations on the value
start repeating near the constant.

**Namespaced object.** In TypeScript and JavaScript, teams often group related
constants in an object with `as const`. This gives a stable namespace and
literal types without runtime class machinery. The cost is that import style
can hide tree shaking or create circular dependencies if the object grows.

**Configuration field.** Some literals are policy, not code. Move them to a
typed configuration object when different environments, tenants, or releases
need different values. The refactoring can still begin with a named constant,
then move the declaration behind configuration while keeping call sites named.

**Protocol registry wrapper.** Use it when a standard owns the values. RFC 9110
defines status code classes and the valid range for HTTP status codes
(https://www.rfc-editor.org/rfc/rfc9110.html#section-15, verified
2026-08-02). A project should not invent names for those values when the
language or platform already ships a registry. Prefer the standard library
constant or enum.

**Test data builder constant.** Use it when the same literal appears in tests
to mean a domain fact. Keep it in the test fixture or builder. Do not promote
test constants into production code unless production code owns the concept.

**Generated constant.** Use it when the source of truth is a schema, OpenAPI
file, protobuf, database enum, or registry. The generated output can provide
named constants, but the source of truth is the schema. Hand editing generated
constants is usually a dead end.

**Unit specific type alias.** Some languages let a project create a thin type
around a primitive. Go can define a named type over an integer. Rust can define
a tuple struct. Swift can define a struct with static members. This variant is
useful when the same raw type has several units, such as bytes, milliseconds,
cents, and percentage basis points. It is heavier than a constant but lighter
than a full domain object.

**Deprecating alias.** Boundary values sometimes need old and new spellings at
the same time. A service may accept an old event name during migration while
emitting the new one. Keep both names explicit, mark the old one as deprecated
in code comments or documentation, and measure remaining use. Do not hide a
compatibility alias behind the new name, because operators need to see which
clients are still sending the old value.

## 9. Known production uses

**Python `http.HTTPStatus`.** Python's standard library defines
`http.HTTPStatus` as an `enum.IntEnum` for HTTP status codes, reason phrases,
and English descriptions. The documentation says the supported status codes
are IANA registered and shows `HTTPStatus.OK.value` as `200`
(https://docs.python.org/3/library/http.html, verified 2026-08-02). This is a
direct production use of symbolic names replacing raw protocol integers while
preserving integer compatibility.

**Go `time` duration constants.** Go's standard `time` package defines
`Nanosecond`, `Microsecond`, `Millisecond`, `Second`, `Minute`, and `Hour` as
duration constants and shows multiplying an integer by `time.Second` instead of
passing a bare count (https://pkg.go.dev/time, verified 2026-08-02). The
documentation also says no `Day` or larger duration constant is defined because
daylight saving time transitions can make such units ambiguous. This is a
production use that names both unit and scale.

**Java `java.util.concurrent.TimeUnit`.** Java SE 21 documents `TimeUnit` as an
enum for duration granularity with constants such as `MILLISECONDS` and
`SECONDS`; its example contrasts `tryLock(50L, TimeUnit.MILLISECONDS)` with
`tryLock(50L, TimeUnit.SECONDS)`
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/TimeUnit.html,
verified 2026-08-02). The enum replaces a bare `50` plus an implicit unit with
an explicit unit argument.

**Kubernetes recommended labels.** Kubernetes documents recommended label keys
such as `app.kubernetes.io/name`, `app.kubernetes.io/instance`, and
`app.kubernetes.io/managed-by` for application metadata
(https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/,
verified 2026-08-02). Kubernetes also documents labels as key/value pairs used
to organize and select object subsets
(https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/,
verified 2026-08-02). Client libraries and platform code often name these
keys locally to avoid raw string drift across manifests, selectors, and
controllers. That last sentence is judgement about common implementation
practice, not a claim made by the Kubernetes documentation.

## 10. Consequences

Judgement. These consequences describe common engineering effects. The right
weight depends on language, ownership, and the stability of the value.

Positive consequences.

- Code speaks in domain terms. `MAX_LOGIN_ATTEMPTS` and
  `LOCKOUT_WINDOW_MINUTES` reveal intent that `5` and `15` hide.
- Duplicate values become findable. A code search for the constant name finds
  the concept, not every unrelated occurrence of the same number.
- Review diff quality improves. Changing a named policy value is easier to
  review than hunting all raw occurrences.
- Unit errors become more visible. Names can include `_MS`, `_SECONDS`,
  `_BYTES`, `_CENTS`, or a type wrapper can remove the unit from the name.
- Boundary contracts become local vocabulary. Protocol names can be kept in one
  adapter rather than scattered across handlers.
- Tests can assert meaning. A test can read "returns too many requests" rather
  than "returns 429."
- Observability can carry policy names. Logs and metrics can include both the
  value and the named rule that produced it.
- Later refactorings get easier. A named constant can move into configuration,
  an enum, or a value object without rewriting every call site.

Negative consequences.

- Poor names make code worse. A vague constant such as `LIMIT` or `VALUE_1`
  hides more than a literal.
- Constant bags become dumping grounds. A global file with unrelated names
  creates coupling and makes ownership unclear.
- Public constants can freeze internal policy. Once downstream code imports a
  value, changing it becomes an API change.
- Equal values can be merged incorrectly. `MAX_RETRIES = 3` and
  `MIN_APPROVERS = 3` should not become `THREE`.
- Indirection can slow reading. A reviewer may need to jump to the declaration
  to see the actual value.
- Compile time constants can be inlined by some languages and build tools.
  Changing a public constant may require downstream rebuilds.
- A constant can hide a need for richer modeling. If code keeps checking
  ranges, parsing formats, or converting units around the constant, a value
  object may be the better design.
- Centralized constants can weaken locality. A one use local rule may become
  harder to understand after it is moved far away.

## 11. Failure modes and misuse

Judgement. The failures below are described as Symptom, Cause, Fix triples so a
reviewer can connect design advice to observable behavior.

**Symptom.** A reader sees `THREE`, `VALUE`, `DEFAULT`, or `MAGIC_NUMBER` and
still asks what the code means.  
**Cause.** The name describes the value or the existence of a constant, not the
domain concept.  
**Fix.** Rename for role and unit, such as `MAX_RETRY_ATTEMPTS`,
`PASSWORD_RESET_TOKEN_BYTES`, or `HTTP_TOO_MANY_REQUESTS`.

**Symptom.** A change to one policy unexpectedly changes another feature.  
**Cause.** Two equal literals were merged into one constant even though they
represent different concepts.  
**Fix.** Split the constant by meaning. Keep equal values separate until a
domain owner says they are the same rule.

**Symptom.** Developers add unrelated values to `Constants` because they cannot
find a better home.  
**Cause.** The declaration site is organized by data type rather than
ownership.  
**Fix.** Move constants next to their owning module, adapter, enum, or policy.
Delete the generic constant bag as entries find homes.

**Symptom.** A service accepts `"prod"` in one endpoint and `"production"` in
another.  
**Cause.** Raw boundary strings are compared in multiple places without a
central parser or enum.  
**Fix.** Create a boundary adapter that maps accepted raw values to one named
internal value and rejects unknown values with a clear error.

**Symptom.** Metrics show two names for the same event, or dashboards split one
series into several near duplicates.  
**Cause.** Event names, tags, or metric labels are magic strings copied by hand.  
**Fix.** Put telemetry names behind constants or typed helper functions owned
by the instrumentation module.

**Symptom.** A timeout change has no effect in production after deployment.  
**Cause.** The value was extracted to a compile time constant but another
module, generated file, or deployment manifest still uses a raw literal.  
**Fix.** Search for the raw value and the concept name. Move cross boundary
policy into typed configuration where deployment uses the same source.

**Symptom.** Operators see `MAX_PAYMENT_AGE` in logs but cannot tell whether it
means minutes, hours, or days.  
**Cause.** The constant name lost the unit, or the logger emits only the name.  
**Fix.** Include unit in the name or type, and log both name and concrete value.

**Symptom.** The code has an enum with one member.  
**Cause.** A single literal was overmodeled as a closed set before a set
existed.  
**Fix.** Collapse to a local constant or inline the literal if no name adds
value.

**Symptom.** A public SDK breaks clients after a constant's value changes.  
**Cause.** A literal from an external contract was treated as local policy.  
**Fix.** Version the contract, keep backward compatible aliases when feasible,
and document raw wire values at the boundary.

**Symptom.** Tests pass while production rejects a payload because `"ContentType"`
was used instead of `"Content-Type"`.  
**Cause.** Tests repeated the same wrong magic string as production code.  
**Fix.** Use a shared boundary constant from the production adapter in tests,
and add an integration test against the real protocol or parser.

## 12. Trade-off matrix

| Force | Replace Magic Literal | Extract Variable | Replace Primitive with Object | Typed Configuration | Inline Literal |
|---|---|---|---|---|---|
| Readability | Strong when name carries role and unit | Strong for one expression | Strong when behavior belongs with value | Medium, name may be far from use | Strong only when value is self explaining |
| Coupling | Reduces coupling to repeated raw values | Local only | Couples callers to a type | Couples callers to config schema | Couples every site to raw contract |
| Consistency | High for one concept | Low beyond one scope | High with validation | High across environments | Low when copied |
| Latency | Neutral for constants | Neutral | Possible allocation or parse cost | Possible lookup cost | Neutral |
| Operability | Good if logs include name and value | Local benefit only | Good if type exposes labels | Good for runtime policy changes | Poor unless each site logs context |
| Cost | Low to medium | Low | Medium to high | Medium | Low now, higher later |
| Team topology | Good for shared vocabulary | Function local | Good for domain ownership | Good for platform owned settings | Poor across teams |
| Cognitive load | Medium, requires vocabulary | Low | Medium, requires type model | Medium | Low at first, high after repetition |
| Change risk | Low for internal policy, high for public constants | Low | Low with validation | Low for runtime policy | High when scattered |

Extract Variable is the closest small refactoring. It names a local expression
without claiming wider reuse. Replace Primitive with Object is the richer move
when the value has behavior, validation, or unit conversion. Typed
Configuration is right when the value varies by deployment or tenant. Inline
Literal is still the best alternative when the value is local and obvious.

## 13. Related and incompatible patterns

**Extract Variable** composes with Replace Magic Literal. A local explanatory
variable can be the first move when the name is not stable enough for a
constant. If the name proves useful outside the function, promote it to a
constant or type.

**Rename Variable** often follows. The first extracted name may be too narrow
or too value focused. A later rename can shift from `TIMEOUT_MS` to
`PAYMENT_AUTHORIZATION_TIMEOUT_MS` when ownership becomes clearer.

**Encapsulate Variable** composes when code outside the owning module should not
read the constant directly. A function such as `retryPolicy.defaultDelay()` can
give the owner room to change storage, configuration, or deprecation policy.

**Replace Primitive with Object** can replace this refactoring when literals
are only one symptom of primitive obsession. A `Duration`, `Money`, `Email`,
`CountryCode`, or `MediaType` type can carry validation and operations that a
constant cannot.

**Introduce Parameter Object** composes when several magic literals travel
together. A timeout, retry count, jitter factor, and backoff cap may belong in a
`RetryPolicy` object rather than four constants.

**Parameterize Function** can be the move out when a named value is not a
single policy but varies by caller. Instead of one constant, pass a named
parameter with a default.

**Inline Variable** and **Inline Function** can remove constants that stopped
earning their place. If a constant has one use and no useful name, inline it.

**Global Constants** as an organizational pattern conflicts with this
refactoring when the global file has no domain ownership. Replace Magic Literal
is about naming meaning. A global bag names storage location.

**Feature Toggle** can replace a boolean or string literal when the value
represents rollout state. Do not turn `"new_checkout"` into only a constant if
the real concept is a managed feature flag with owners, rollout data, and
expiry.

## 14. Refactoring path in and out

Path in.

1. Find the literal and read the surrounding code before naming it.
2. Search for the same raw value. Include tests, configuration templates,
   queries, manifests, and telemetry helpers.
3. Decide which occurrences share the same meaning. Equal values are not enough.
4. Choose the smallest owning scope. Prefer local, then module, then package,
   then public API.
5. Declare the name with the raw value. Include unit in the name when the type
   does not carry the unit.
6. Replace one use site and run the smallest relevant test.
7. Replace the rest of the use sites that share the same meaning.
8. Add or adjust tests that cover boundary parsing, output, or policy behavior.
9. Search again for the raw literal and confirm remaining occurrences mean
   something else or are valid non-applicability cases.
10. If callers start performing validation or conversion around the constant,
    continue to Replace Primitive with Object or Introduce Parameter Object.

Path out.

1. Identify constants with one use, vague names, or no domain meaning.
2. Inline the value when the literal is clearer than the name.
3. Split a constant when equal values have diverged in meaning.
4. Move public constants behind functions when callers should not depend on
   storage or policy.
5. Move environment specific constants to typed configuration.
6. Replace groups of constants with a value object or policy object when they
   change together.
7. Delete unused constants after the code search and test suite confirm no use
   remains. Cross reference Remove Dead Code.

The safest path is incremental. Replace one concept at a time, run tests, then
repeat. Large mechanical sweeps can merge unrelated meanings because they see
only equal values.

A useful migration pattern is "name, replace, then model." First, introduce a
name that changes no behavior. Second, replace matching use sites and keep a
small list of raw occurrences that intentionally remain. Third, look at the new
call sites. If they cluster around parsing, formatting, validation, or unit
conversion, promote the named value into a type or adapter. If they cluster
around environment differences, move it to typed configuration. If they do not
cluster, keep the constant small and local.

Another useful path is "one boundary at a time." For example, do not replace
every `"production"` string in a service in one sweep. Start at the HTTP or
message boundary, create `DeploymentEnvironment.Production`, parse raw input
there, and pass the named value inward. Then replace internal comparisons. Last,
change emitted values. This order keeps external behavior stable while the
internal vocabulary improves.

## 15. Testing and verification

Judgement. Testing should prove that names did not alter behavior and that the
new declaration site preserves boundary contracts.

Use characterization tests when the literal sits in old code without good
coverage. Capture current behavior before extraction, especially for boundary
values such as status codes, event names, database enum strings, and header
names. After replacement, the same tests should pass.

Use golden tests with care. If a named constant changes a serialized value, the
golden file should show the raw output. The constant name helps the source code,
but users and peer systems see the literal. Assert both when it matters: the
domain code uses the named value, and the boundary output is the agreed raw
value.

Use parameterized tests for closed sets. For an enum or union, iterate through
every named value and prove that parsing, serialization, and display are
stable. This catches missing cases after a new constant is added.

Use mutation testing or negative tests for unknown values at boundaries. A
parser should reject `"prodution"` when only `"production"` is allowed. Without
that test, extracting constants can create false confidence while raw typos
still slip through from clients.

Use compile time checks where the language offers them. TypeScript literal
unions, Rust enums, Swift enums, Java enums, and Python `Enum` can make illegal
states harder to express. Compile time checks are not substitutes for boundary
tests because external input still arrives as raw text or bytes.

Use snapshot review for telemetry names. Metric names, event names, and label
keys can fragment dashboards when changed. A small test that lists emitted
metric names can catch accidental renames.

Test doubles should preserve the named vocabulary. A fake service that returns
`429` should use the same named status as the production adapter when the test
is about rate limiting. If the test is about protocol decoding, raw literals
belong in the fixture because they represent external input.

What became easier: policy changes, repeated boundary values, and unit clarity.
What became harder: detecting unused public constants, proving no unrelated
equal values were merged, and keeping constant names from becoming API by
accident.

## 16. Observability signals

Judgement. The refactoring has no built in observability. Add signals where the
named value controls runtime behavior or crosses a boundary.

Log the policy name and value when a decision depends on the literal. A retry
worker can log `policy=DEFAULT_RETRY_DELAY_MS value_ms=30000` during debug
events. A quota handler can log `decision=TOO_MANY_REQUESTS status=429` when it
rejects a request. Do not log secrets or private data under the banner of
observability.

Trace boundary adapters. A span that parses a user supplied state, media type,
or event name should record whether parsing found a known value, a deprecated
value, or an unknown value. Keep tag cardinality bounded. Do not put arbitrary
raw strings into metric labels.

Measure fallback and unknown value rates. A healthy instance has low or zero
unknown protocol values, no deprecated spellings after migration, and stable
metric label cardinality. A failing instance shows rising unknown values, split
series caused by typo variants, or policy names that no longer match the
documented value.

Expose configuration drift for values that moved out of code. If
`DEFAULT_RETRY_DELAY_MS` becomes `retry.delay_ms` in configuration, dashboards
should show the effective value per environment. This helps operators
distinguish a code bug from a rollout or configuration mismatch.

Emit both symbolic and raw forms at boundaries when safe. Symbolic form helps
humans search code. Raw form helps compare traffic, standards, and external
logs. For example, `http_status_name=TOO_MANY_REQUESTS` and `http_status=429`
are more useful together than either alone.

## 17. Security and privacy implications

Judgement. Replace Magic Literal is usually neutral for security by itself. It
can reduce mistakes around boundary values, but it can also make sensitive
values easier to leak if used carelessly.

Do not extract secrets into constants. API keys, passwords, tokens, salts,
private URLs, and customer identifiers belong in secret storage, runtime
configuration, or test fixtures with fake values. A named constant can make a
secret look intentional and easier to copy.

Use names to harden allowlists. Header names, media types, algorithms, scopes,
roles, and event names are safer when parsed through a known set rather than
compared as scattered strings. The gain comes from the parser or enum, not from
the constant alone.

Be careful with authorization roles. `ADMIN = "admin"` can be a useful boundary
constant, but raw role strings in application code often signal a missing
authorization model. Prefer a role type or policy object when permissions have
behavior.

Avoid logging raw literals from untrusted input as metric labels. A constant
for a known label key is fine. A raw user supplied value can explode
cardinality or leak private data. Map unknowns to a fixed value such as
`unknown`.

Watch public constants in SDKs. If a client package exposes constants for
security relevant protocol values, those constants become part of the public
contract. Deprecate old values carefully. Keep aliases when protocol
compatibility requires them.

This refactoring is silent on cryptography. It does not make an algorithm,
salt length, token size, or timeout safe. It only gives the value a name. The
security review still has to validate the chosen value and the threat model.

## Code examples

TypeScript is idiomatic for string unions and `as const` objects. This example
names status and retry policy values while preserving raw boundary values.

```typescript
const HttpStatus = {
  TooManyRequests: 429,
} as const;

const RetryPolicy = {
  DefaultDelayMs: 30_000,
  MaxAttempts: 3,
} as const;

type HttpStatusCode = (typeof HttpStatus)[keyof typeof HttpStatus];

function retryHeader(attempts: number): string | undefined {
  if (attempts >= RetryPolicy.MaxAttempts) {
    return undefined;
  }
  return String(RetryPolicy.DefaultDelayMs);
}

function responseForQuota(used: number, limit: number): HttpStatusCode | 200 {
  return used > limit ? HttpStatus.TooManyRequests : 200;
}

console.log(responseForQuota(11, 10), retryHeader(1));
```

Python is idiomatic when the value belongs to an enum or module constant. This
example uses the standard library status enum and a local policy constant.

```python
from http import HTTPStatus

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


def login_decision(failed_attempts: int) -> tuple[int, str]:
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        return (
            HTTPStatus.TOO_MANY_REQUESTS,
            f"try again in {LOCKOUT_WINDOW_MINUTES} minutes",
        )
    return (HTTPStatus.OK, "continue")


print(login_decision(5))
```

Go is idiomatic for unit constants and typed aliases. This example uses
`time.Duration` instead of a bare millisecond count.

```go
package main

import (
	"fmt"
	"time"
)

const (
	maxAttempts       = 3
	defaultRetryDelay = 30 * time.Second
)

func nextDelay(attempt int) (time.Duration, bool) {
	if attempt >= maxAttempts {
		return 0, false
	}
	return defaultRetryDelay, true
}

func main() {
	delay, ok := nextDelay(1)
	fmt.Println(ok, int64(delay/time.Millisecond))
}
```

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Organizing Data," page 204,
  "Replace Magic Number with Symbolic Constant."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings,"
  "Replace Magic Literal."
- Martin Fowler, "Replace Magic Literal," refactoring catalog,
  https://refactoring.com/catalog/replaceMagicLiteral.html, verified
  2026-08-02.
- Python Software Foundation, "`http` HTTP modules," Python 3 documentation,
  https://docs.python.org/3/library/http.html, verified 2026-08-02.
- Go project, "`time` package," Go standard library documentation,
  https://pkg.go.dev/time, verified 2026-08-02.
- Oracle, "`java.util.concurrent.TimeUnit`," Java SE 21 API documentation,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/TimeUnit.html,
  verified 2026-08-02.
- Kubernetes documentation, "Recommended Labels,"
  https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/,
  verified 2026-08-02.
- Kubernetes documentation, "Labels and Selectors,"
  https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/,
  verified 2026-08-02.
- R. Fielding, M. Nottingham, J. Reschke, editors, "RFC 9110. HTTP Semantics,"
  section 15, https://www.rfc-editor.org/rfc/rfc9110.html#section-15,
  verified 2026-08-02.
