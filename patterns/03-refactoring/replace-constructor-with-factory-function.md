---
name: Replace Constructor with Factory Function
slug: replace-constructor-with-factory-function
family: 03-refactoring
category: Refactoring
aliases: [Replace Constructor with Factory Method, Static Creation Function, Named Constructor]
first_described: "Fowler 2018"
maturity: canonical
related: [factory-method, abstract-factory, builder, introduce-parameter-object, change-function-declaration]
incompatible_with: []
verified: 2026-08-02
---

# Replace Constructor with Factory Function

## 1. Name, aliases, and lineage

The canonical name in this repository is **Replace Constructor with Factory
Function**. Martin Fowler lists the refactoring under that name in the second
edition of *Refactoring. Improving the Design of Existing Code*, Addison-Wesley,
2018, chapter 11, "Refactoring APIs." Fowler's online catalog page gives the
same name and lists **Replace Constructor with Factory Method** as an alias,
showing a constructor call replaced by a named creation call
(https://refactoring.com/catalog/replaceConstructorWithFactoryFunction.html,
verified 2026-08-02).

The name varies by language community. Java programmers often say **static
factory method**, following Joshua Bloch's terminology in *Effective Java*, 3rd
edition, Addison-Wesley, 2018, Item 1, "Consider static factory methods instead
of constructors." JavaScript, TypeScript, Python, Go, Rust, and Swift code often
uses the shorter phrase **factory function**, because a named function can sit
outside the type or on the type. Some languages also use **named constructor**
for the same move when the function is attached to the type, as with Python
class methods or Swift static methods.

This refactoring is related to, but not the same as, the Gang of Four Factory
Method pattern. Factory Method in the GoF catalog is a polymorphic creation
hook on a creator hierarchy. Replace Constructor with Factory Function is an
API refactoring. It changes how callers ask for an object. The result may be a
plain free function, a static method, a class method, an associated function, or
a small factory object. It does not require inheritance.

The lineage matters because the refactoring solves an API problem before it
solves a design pattern problem. A constructor has a fixed name, tied to the
type. A factory function has a name chosen by the API author. That name can
carry intent such as `from_json`, `new_request`, `parse`, `empty`, `of`,
`create_user`, or `with_context`. The refactoring earns its place when the
construction act needs that extra contract.

## 2. Problem and context

A constructor is too narrow for the creation contract the type now needs. The
call site still says "make this type," but the true operation has become more
specific. It may validate input, normalize data, choose a subtype, return a
cached value, attach a default dependency, hide an internal representation, or
signal failure in a way the language constructor cannot express.

The problem often appears gradually. A class starts with a direct constructor:

```text
const user = new User(email, password);
```

Later, password hashing is added. Later, email normalization is added. Later,
the caller must pass tenant defaults. The constructor grows, or the same
preparation code spreads across controllers, tests, import jobs, and command
line scripts. The class is still called `User`, but callers no longer need "a
raw user object." They need "a user created by the application rule."

The constructor can also become too public. A type may have invariants that
must never be bypassed, but a public constructor lets any caller build an
invalid instance. A factory function can be the public path while the
constructor becomes private, package-private, module-private, or documented as
internal.

The context for the refactoring has three parts.

- Callers should ask for a meaningful creation operation, not for storage layout.
- Construction has rules that should live in one place.
- The old constructor call can be migrated without changing the object's visible
  behaviour.

There is also a timing context. This refactoring is easiest before a constructor
becomes a widely copied public habit. Once examples, tutorials, generated code,
tests, and third-party packages all call the constructor directly, the factory
must compete with existing muscle memory. That does not make the refactoring
wrong, but it changes the rollout from a local edit into an API migration. For
that reason, a team should consider this refactoring early when it sees the
first non-trivial construction rule. Waiting until the constructor has ten
parameters and three kinds of caller-side preparation makes the final design
more obvious, but the change becomes broader.

The deeper smell is not "there is a constructor." The smell is that the
constructor is being asked to communicate more than a constructor name can
carry. Type names name nouns. Factory names can name actions, sources, formats,
and policies. `Invoice.from_xml`, `Session.resume`, `Token.for_scope`, and
`Request.with_context` are different creation stories even if they end at the
same runtime type. When that story matters to correctness, the API should carry
it in the name rather than leave it in comments or caller convention.

Outside that context, a factory function is ceremony. A direct constructor is a
good API when the object is simple, the constructor name is clear enough, and
the type has no hidden creation policy.

## 3. Forces

Engineering judgement. This dimension weighs pressures that vary by codebase,
so the claims here are design reasoning rather than sourced history.

- **Clarity at call sites.** The refactoring favours clarity when the factory
  name says what the constructor cannot say. `Money.from_decimal("12.30",
  "usd")` carries more intent than `Money("12.30", "usd")`. It hurts clarity
  when the name is vague, such as `create` on a type with one obvious
  constructor.
- **Invariant protection.** The refactoring favours stronger invariants because
  creation can pass through validation and normalization before an instance
  escapes. It sacrifices the ability to allocate the type freely in tests and
  small scripts.
- **Coupling.** It can reduce coupling to concrete representation because the
  factory may return an interface, an alias, a private subtype, or a cached
  instance. It can increase coupling to a module-level factory name if the
  module becomes a shared dependency hotspot.
- **Consistency.** It favours consistency when every caller uses the same
  creation path. It sacrifices consistency if both the public constructor and
  the new factory remain equally blessed for too long.
- **Latency.** It is usually neutral. A factory call is not slower in a way that
  matters for ordinary object creation. It can add cost when it performs input
  and output, registry lookup, schema loading, or cache locking.
- **Operability.** It favours operability when the factory becomes the one place
  to log creation failures, count invalid input, and label subtype selection. It
  hurts operability when factories hide work such as network calls behind a name
  that reads like plain allocation.
- **Cost.** It lowers change cost when construction policy evolves. It raises
  migration cost because existing call sites must move from `new Type(...)` or
  `Type(...)` to the named function.
- **Team topology.** It favours platform teams that own core invariants and
  application teams that consume those invariants. It can frustrate teams that
  need quick test fixtures if the only public creation path performs all
  production checks.
- **Cognitive load.** It lowers local cognitive load when the name is precise.
  It raises global load because readers must learn which factory names are
  canonical and which constructors are internal.

The refactoring favours correctness and API meaning over mechanical
minimalism. It should pay rent every time a caller reads the creation line.

Two forces often decide the outcome in practice.

First, the design must decide whether invalid state is ever allowed to exist.
Some domains gain a lot from forbidding invalid instances at the boundary.
Money, security principals, scoped tokens, normalized email addresses, and
database URLs are easier to reason about when every instance has passed through
one creation rule. Other domains need temporary invalid states because the
object is a draft, a parser product, or a repair target. In those domains the
factory should not pretend the object is complete. The API may need a separate
draft type, a builder, or a validation result.

Second, the design must decide where policy belongs. A factory function is a
policy boundary. That is useful when the policy is owned by the type or the
module. It is less useful when policy belongs to the caller, such as choosing a
retry budget, selecting a tenant, or injecting a clock. Caller-owned policy
should be passed in explicitly or configured in a provider. Hiding it inside a
factory makes tests brittle and production behaviour hard to explain.

## 4. Applicability and non-applicability

Reach for this refactoring when the following hold.

- A constructor has boolean, enum, or sentinel arguments whose meaning is
  invisible at the call site, and named factories would split the meanings into
  separate calls.
- Construction requires validation, normalization, defaulting, or derived fields
  that should not be repeated by callers.
- A type needs more than one creation route, such as `from_json`, `from_id`,
  `from_parts`, `empty`, and `copy_of`.
- The API needs to return an existing instance, pooled instance, interned value,
  proxy, subclass, or interface without forcing callers to know that policy.
- The constructor cannot report failure in the desired way. Go constructors do
  not exist as language features, so `NewType(...) (Type, error)` is idiomatic.
  Java constructors cannot return cached objects. Python constructors can bend
  `__new__`, but a class method is usually easier to read.
- A public constructor exposes representation details that the owner wants to
  change later.
- The constructor name is forced by the type, but the operation has a domain
  name that would be more precise.
- Call sites are already running a preparation sequence before every
  constructor call.

Do NOT reach for this refactoring in the following non-applicability cases.

- **The constructor is clear and has no policy.** If `Point(x, y)` creates a
  plain value with no validation beyond types, a factory name adds another
  lookup for no gain.
- **The factory would be named only `create` and do nothing else.** A
  no-policy wrapper around a public constructor is noise. Keep the constructor.
- **The problem is too many optional fields.** Use Builder or Introduce
  Parameter Object. A factory with ten optional parameters is the old
  constructor under another name.
- **The problem is choosing among families of related objects.** Use Abstract
  Factory when several products must be selected together.
- **The problem is an algorithm choice after construction.** Use Strategy.
  Creation should not become a dumping ground for behaviour selection.
- **The type is a data transfer object owned by a serializer.** Many serializers
  need a simple public constructor or field-based creation. A factory may fight
  the tool.
- **The constructor is part of a stable public binary API.** Replacing it may be
  a breaking change. Add a factory first, deprecate the constructor, then remove
  it on the next allowed major release.
- **The factory would perform hidden input and output.** Prefer a name that says
  the operation is loading, opening, connecting, or fetching. Allocation-looking
  names should not mask remote work.
- **Tests need invalid states by design.** For parser, validator, and migration
  tests, a private constructor can make invalid fixtures hard to create. Keep a
  test-only builder or an internal unsafe constructor if those tests are
  legitimate.
- **The language already has a clear named constructor convention for the case.**
  In Rust, `From`, `TryFrom`, `Default`, and `new` may already express the
  creation route. A custom factory name should add domain meaning.
- **The type is meant to be subclassed by consumers.** A private constructor can
  make subclassing impossible or awkward. If subclassing is part of the public
  contract, prefer a protected constructor plus named factories for common
  cases.
- **The main need is dependency wiring.** A factory function should not become a
  miniature dependency injection container. If the object needs a repository,
  logger, clock, and message bus, pass those dependencies through the normal
  wiring mechanism.
- **The current constructor is generated code.** Code generators may overwrite
  hand edits or regenerate direct constructor usage. Configure the generator
  first, or put the factory in a stable wrapper type outside the generated
  file.
- **The factory name would encode a temporary migration detail.** Names such as
  `createV2` or `newNewOrder` age poorly. Use a domain name for the new route
  and keep versioning in package, endpoint, or deprecation policy.

The applicability test can be phrased as a question. If a new engineer sees the
factory name in a call site, do they learn a rule that would otherwise be
hidden? If the answer is yes, the refactoring probably has value. If the answer
is no, the factory may be a wrapper looking for a reason.

## 5. Structure

The refactoring has five participants.

- **Client call site.** The code that currently invokes the constructor. It is
  the unit being migrated. In a large codebase there may be hundreds of these,
  so the migration path matters as much as the final shape.
- **Constructed type.** The object being created. After the refactoring, this
  type may keep a private constructor, keep a deprecated public constructor, or
  expose no direct constructor at all if the language permits that.
- **Factory function.** The named creation operation. It accepts input in the
  caller's natural form, applies creation policy, and returns the constructed
  type or a declared abstraction.
- **Creation policy.** The validation, normalization, subtype selection,
  defaulting, caching, instrumentation, or error mapping that makes the factory
  worth having.
- **Internal constructor or builder.** The allocation mechanism the factory uses
  after it has made the policy decision. It should be smaller and less public
  than the factory API.

The relationship is simple. Callers depend on the factory function. The factory
depends on the internal constructor. The constructed type depends on its own
invariants, not on caller discipline. When the refactoring is complete, normal
production code has one sanctioned path into a valid instance.

This structure is not always a class wrapper. In Go, the factory is often a
free function named `NewType`. In Python, it may be a `@classmethod`. In Rust,
it may be an associated function returning `Self` or `Result<Self, Error>`. In
TypeScript, it may be a static method paired with a private constructor. In
JavaScript, it may be an exported function that returns a frozen object.

## 6. ASCII structure diagram

```text
  BEFORE

  +-------------------+        calls         +----------------------+
  | Client A          | -------------------> | public constructor   |
  |-------------------|                      | Type(raw arguments)  |
  | trims email       |                      +----------------------+
  | checks tier       |                                |
  +-------------------+                                v
                                                   +---------+
  +-------------------+        calls              | Type    |
  | Client B          | ------------------------> | object  |
  |-------------------|                           +---------+
  | lowercases email  |
  | picks quota       |
  +-------------------+

  AFTER

  +-------------------+                      +----------------------+
  | Client A          |                      | Factory function     |
  |-------------------|                      | createAccount(input) |
  | createAccount()   | -------------------> |----------------------|
  +-------------------+                      | validate             |
                                             | normalize            |
  +-------------------+                      | choose defaults      |
  | Client B          |                      +----------+-----------+
  |-------------------|                                 |
  | createAccount()   | --------------------+            v
  +-------------------+                     |   +------------------+
                                            +-> | private/internal |
                                                | constructor      |
                                                +--------+---------+
                                                         |
                                                         v
                                                    +---------+
                                                    | Type    |
                                                    | object  |
                                                    +---------+
```

## 7. Dynamics

The runtime flow is a policy checkpoint followed by allocation. The factory may
return without allocation when it uses caching or interning, and it may fail
before allocation when input is invalid.

```text
  Client                 Factory function          Internal constructor
    |                            |                           |
    | createAccount(input)       |                           |
    |--------------------------->|                           |
    |                            | validate raw input        |
    |                            | normalize fields          |
    |                            | derive missing values     |
    |                            |                           |
    |                            | cache hit?                |
    |                            |------ yes ----------------|
    |                            | return cached object      |
    |<---------------------------|                           |
    |                            |                           |
    | createAccount(other input) |                           |
    |--------------------------->|                           |
    |                            | validate raw input        |
    |                            | normalize fields          |
    |                            | cache miss                |
    |                            |-------------------------->|
    |                            |     allocate valid state  |
    |                            |<--------------------------|
    |<---------------------------|                           |
```

The sequence should have one visible property. All policy runs before the object
escapes. If the factory returns a half-valid object that callers must repair,
the refactoring has failed. If the factory performs work that a caller would not
expect from a creation name, the name should change to match that work.

Constructor replacement also changes failure timing. A public constructor may
have allowed invalid state to travel for several calls before failing. A factory
usually fails earlier. That is good for correctness, but it can expose latent
bugs during migration because call sites that formerly smuggled bad data now
raise at creation time.

## 8. Implementation variants

**Static factory method on the type.** The factory sits on the class and the
constructor becomes private or deprecated. This fits Java and TypeScript. Bloch
documents several advantages of static factory methods over constructors in
*Effective Java*, 3rd edition, Item 1, including named creation, return-type
flexibility, and instance control. Engineering judgement. Use this variant when
callers already import the type and the factory is part of that type's public
vocabulary.

```typescript
type Tier = "free" | "paid";

class Account {
  private constructor(
    readonly email: string,
    readonly tier: Tier,
    readonly quota: number,
  ) {}

  static create(email: string, tier: Tier): Account {
    if (!email.includes("@")) {
      throw new Error("email required");
    }
    const quota = tier === "paid" ? 1000 : 100;
    return new Account(email.toLowerCase(), tier, quota);
  }
}

const acct = Account.create("ME@example.com", "paid");
if (acct.email !== "me@example.com" || acct.quota !== 1000) {
  throw new Error("factory failed");
}
```

**Class method as named constructor.** Python commonly uses `@classmethod` when
the factory should respect subclasses. The method receives `cls`, so a subclass
can inherit the factory and receive its own type.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str

    @classmethod
    def from_decimal(cls, amount: str, currency: str) -> "Money":
        whole, dot, frac = amount.partition(".")
        if not whole.isdecimal() or (dot and not frac.isdecimal()):
            raise ValueError("decimal amount required")
        cents = int(whole) * 100 + int((frac + "00")[:2])
        return cls(cents, currency.upper())


price = Money.from_decimal("12.30", "usd")
assert price == Money(1230, "USD")
```

**Free function returning value and error.** Go has no constructor syntax, and
the standard convention is an exported `NewType` function. The factory can
return `(T, error)` or `(*T, error)`, which keeps invalid objects out of normal
flow.

```go
package main

import "fmt"

type Token struct {
    Value string
    Scope string
}

func NewToken(value string, scope string) (Token, error) {
    if value == "" || scope == "" {
        return Token{}, fmt.Errorf("value and scope required")
    }
    return Token{Value: value, Scope: scope}, nil
}

func main() {
    token, err := NewToken("abc", "read")
    if err != nil {
        panic(err)
    }
    if token.Scope != "read" {
        panic("bad scope")
    }
}
```

**Associated function with fallible creation.** Rust code often uses `new`,
`from_*`, `try_from`, or `parse` as associated functions. When creation can
fail, returning `Result<Self, Error>` makes the failure part of the type
contract. That is preferable to constructing a value and asking callers to call
`is_valid()` later.

**Factory returning an interface or protocol.** The factory's declared return
type can be an interface even when the internal constructor names a concrete
class. This fits plugin, driver, and adapter code. The benefit is representation
hiding. The cost is that callers lose access to concrete methods unless the
interface is shaped well.

**Factory with instance control.** A factory can return a cached object,
interned value, singleton scoped to a context, or pooled resource. Java's
`Integer.valueOf(int)` is a named API example whose documentation says it
returns an `Integer` instance for the supplied value
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html,
verified 2026-08-02). Engineering judgement. Cache only when identity and
lifetime are part of the contract, or when returning a shared immutable value is
invisible to callers.

**Factory paired with private raw constructor.** The raw constructor remains so
the type can set final fields, participate in serialization, or keep generated
code happy, but it is private or internal. This is the clean final state when
the language supports access control.

**Migration factory beside public constructor.** For public APIs, add the
factory first and leave the constructor in place with a deprecation notice.
Move callers gradually. Delete the constructor only when the compatibility
policy permits it.

**Factory object for stateful creation.** Sometimes the creation policy needs
state: a clock, a tenant identifier, a random source, a pool, or a registry. A
free function can accept those values, but long dependency lists are a warning.
Move the state into a small factory object when the state is stable across many
creations. Keep that object narrow. If it starts owning unrelated creation
routes, split it by product family or by bounded context.

**Module function over class method.** In languages with modules as the main
unit of encapsulation, a module-level function can be cleaner than a static
method. It lets the module hide several concrete types and return one exported
interface. The trade-off is discoverability. Some readers search for creation
on the type, while others search for exported functions in the module. Pick one
style per package and repeat it.

**Parsing factory.** A parsing factory accepts text or bytes and returns a
domain value. It should be named as parsing, not plain creation, because parsing
has failure and format semantics. The result should not carry raw input unless
the domain needs it. Keep parse errors specific enough for callers to repair
input, but avoid leaking private source data in error strings.

**Copying factory.** A copying factory creates a value from another collection,
record, or object. It is useful when the new type must take ownership, freeze
mutable input, or normalize field names. The caller learns that a boundary is
being crossed. A direct constructor may look like it stores references, while a
factory named `copy_of` or `from_record` communicates the ownership move.

## 9. Known production uses

**Django, `User.objects.create_user()`.** Django's authentication
documentation tells callers that the direct way to create users is the included
`create_user()` helper and shows `User.objects.create_user(...)`. The same page
warns that Django stores password hashes rather than raw passwords and says not
to manipulate the password attribute directly, which is why the helper is used
(https://docs.djangoproject.com/en/5.2/topics/auth/default/#creating-users,
verified 2026-08-02). This is a production framework using a named creation
operation so callers do not bypass password policy.

**SQLAlchemy, `create_engine()`.** SQLAlchemy's Core documentation lists
`sqlalchemy.create_engine(url, **kwargs)` and describes it as creating a new
`Engine` instance. The same page shows URL strings for multiple database
dialects, such as PostgreSQL, MySQL, Oracle, Microsoft SQL Server, and SQLite,
all passed through the same creation function
(https://docs.sqlalchemy.org/en/20/core/engines.html, verified 2026-08-02).
This is a named factory hiding dialect parsing, pool creation, and engine
configuration behind one public API.

**Go standard library, `http.NewRequestWithContext()`.** The Go `net/http`
package documents `NewRequestWithContext(ctx, method, url, body)` as returning
a new `*Request` and an `error`
(https://pkg.go.dev/net/http#NewRequestWithContext, verified 2026-08-02).
This is the Go form of the pattern: a named factory function creates a
validated request object and reports failure through the language's ordinary
error return.

**React, `createElement()`.** React's API reference says `createElement` creates
a React element and serves as an alternative to JSX. It documents the call shape
`createElement(type, props, ...children)`
(https://react.dev/reference/react/createElement, verified 2026-08-02). This is
a factory function for a value whose internal representation is owned by the
library rather than by application constructors.

**Java, `Integer.valueOf(int)`.** The Java SE 21 API documents
`Integer.valueOf(int)` as returning an `Integer` instance representing the
given `int` value
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html,
verified 2026-08-02). The production lesson is not that every value wrapper
needs such a method. The lesson is that a named factory can preserve the public
contract while the implementation decides how instances are supplied.

## 10. Consequences

Engineering judgement. Consequences depend on API maturity, language rules,
and how much construction policy exists.

Positive.

- Call sites can say the domain operation: `create_user`, `from_decimal`,
  `parse`, `with_context`, `empty`, or `copy_of`.
- Invariants move from caller convention into one creation path.
- The constructed type can hide its representation and change it later.
- The API can return an interface, subtype, cached value, pooled object, or
  proxy without changing the caller's creation expression.
- Creation failures can use the language's best error style, such as Go's
  `(value, error)` or Rust's `Result`.
- Tests can target the creation policy directly instead of repeating setup code
  across test cases.
- Telemetry can be placed at the factory boundary, where all valid production
  construction passes.
- A compatibility migration can be gradual: add factory, migrate callers,
  deprecate constructor, remove constructor later.

Negative.

- There is another public API name to learn.
- If the old constructor remains public, two creation paths can diverge.
- A vague factory name hides rather than clarifies. `create` is often weaker
  than a direct constructor unless the type has no constructor syntax.
- Some frameworks, serializers, object mappers, and dependency injection tools
  expect constructors. A factory may need adapter configuration.
- Subclassing can become more complex when constructors are private.
- Test fixtures may need a separate fixture factory or builder.
- A factory can hide expensive work behind an innocent name.
- Refactoring a public constructor can break callers in languages where named
  arguments, reflection, or binary compatibility expose constructor shape.

The net result is a better API when construction has meaning. It is a worse API
when construction is plain allocation.

## 11. Failure modes and misuse

Engineering judgement. These are recurring failure shapes with observable
symptoms, causes, and fixes.

**Symptom.** New objects sometimes have different validation behaviour
depending on which part of the application created them.
**Cause.** The factory was added, but the public constructor stayed in active
use and still bypasses policy.
**Fix.** Move all production call sites to the factory. Restrict the constructor
with access control, or deprecate it and add a lint rule or search gate for new
uses.

**Symptom.** A call named `createOrder()` opens network connections, performs
remote authorization, or writes database rows, causing slow tests and timeouts.
**Cause.** The factory became a service operation rather than a creation
operation.
**Fix.** Rename the operation to `load`, `open`, `register`, or `provision`, or
split pure object creation from external work.

**Symptom.** Callers cannot build common test data without large setup graphs.
**Cause.** The factory centralizes production invariants but offers no testing
path for deliberate edge states.
**Fix.** Add a test data builder, fixture factory, or internal unsafe
constructor limited to test packages.

**Symptom.** The factory parameter list grows longer than the old constructor
and accumulates nullable values.
**Cause.** The refactoring was used to disguise a construction API that really
needs a parameter object or builder.
**Fix.** Introduce Parameter Object for coherent input groups, or use Builder
for optional parts.

**Symptom.** A factory named `create` returns different concrete subtypes based
on a string, and callers immediately branch on the subtype.
**Cause.** The factory is doing selection, but the returned abstraction does
not support the work callers need.
**Fix.** Move the missing operations onto the abstraction, split the factories
by intent, or use explicit typed factories where callers need concrete
behaviour.

**Symptom.** A memory graph shows many objects retained by a map inside the
factory module.
**Cause.** Instance control was added as an unbounded cache.
**Fix.** Bound the cache, use weak references where suitable, or remove caching
if object identity was not part of the contract.

**Symptom.** An API migration breaks reflection based code, serializers, or
dependency injection wiring even though normal compilation passes.
**Cause.** Those tools were constructing the type by constructor metadata rather
than by source call sites.
**Fix.** Audit reflective creation before removing the constructor. Provide a
tool adapter, keep a no-argument constructor for the tool, or map the tool to
the factory.

**Symptom.** The type has `fromJson`, `parseJson`, `ofJson`, and
`createFromJson`, all doing similar work.
**Cause.** Factory naming was not treated as an API design decision.
**Fix.** Pick a naming convention per module, migrate old names with
deprecations, and keep one canonical factory for each creation route.

## 12. Trade-off matrix

Engineering judgement. The matrix compares named alternatives across the forces
from dimension 3.

| Force | Factory Function | Direct Constructor | Builder | Abstract Factory | GoF Factory Method | Dependency Injection Provider |
|---|---|---|---|---|---|---|
| Call-site clarity | High when name is specific | High for simple values | Medium, many calls | Medium | Medium, hidden behind creator | Medium, wiring may be distant |
| Invariant protection | Strong if constructor is restricted | Weak if public callers can bypass | Strong at build end | Strong for families | Strong through hook | Strong if provider is canonical |
| Coupling to representation | Low, return type can hide it | High, caller names type | Medium | Low | Low | Low |
| Runtime subtype choice | Good | Poor | Poor | Good for families | Good by subclass dispatch | Good by configuration |
| Optional parameter handling | Medium | Poor | Strong | Poor | Poor | Medium |
| Failure reporting | Strong, can return result type | Language limited | Strong at build end | Strong | Strong | Strong |
| Latency visibility | Good if measured at factory | Allocation is obvious | Assembly may be spread out | Hidden by factory | Hidden by hook | Hidden by container |
| Migration cost | Medium, callers change | None | Medium to high | High | High if hierarchy absent | Medium |
| Team ownership | Good for central policy | Poor for shared rules | Good for complex products | Good for platform families | Good for frameworks | Good for apps with containers |
| Cognitive load | Medium | Low | Medium | High | High | Medium to high |

Reading of the table. Direct constructors win when creation is simple. Factory
functions win when creation has one named policy. Builder wins when the problem
is many optional parts. Abstract Factory wins when several products must agree.
GoF Factory Method wins when a framework owns an algorithm and subclasses own
one creation hook. Dependency injection providers win when application wiring
already owns object selection.

## 13. Related and incompatible patterns

**Factory Method.** Related but narrower. Factory Method is a creational design
pattern using polymorphic dispatch on a creator. Replace Constructor with
Factory Function may produce that shape, but it may also produce a free
function or static method with no inheritance.

**Abstract Factory.** A factory function can be one operation on an abstract
factory. Use Abstract Factory when the caller needs a family of related
products, such as driver, connection, statement, and metadata objects that must
match.

**Builder.** Builder replaces constructors when the problem is staged assembly
or many optional parameters. Factory functions and builders compose well: a
factory can return a preconfigured builder, or a builder can call a private
constructor after validation.

**Introduce Parameter Object.** This often comes before the refactoring when the
constructor has a long parameter list. First group the input into a meaningful
request object, then decide whether creation should be named.

**Change Function Declaration.** Adding the factory and migrating callers is an
API change. Renaming `create` to `from_decimal` is also Change Function
Declaration.

**Encapsulate Variable and Encapsulate Record.** These compose with the pattern
when the reason for the factory is invariant protection. First stop exposing
mutable fields, then control creation.

**Singleton.** Compatible only when shared identity is explicit in the factory
contract. A factory that secretly returns a process-wide singleton surprises
tests and tenant isolation.

**Service Locator.** Usually incompatible. A factory that reaches into a global
locator hides dependencies at the same moment it claims to clarify creation.
Prefer passing dependencies to the factory or to a small factory object.

**Prototype.** A substitute when the desired instance is best described by
copying an exemplar rather than by passing constructor arguments.

## 14. Refactoring path in and out

Introduce the refactoring in small steps.

1. Pick one constructor call shape that is causing trouble. Do not begin with a
   global rewrite.
2. Name the creation policy. If no better name than `create` appears, recheck
   applicability. A weak name is a warning sign.
3. Add the factory beside the constructor. Have it call the existing constructor
   after applying one small policy, such as normalization or validation.
4. Move one caller to the factory and run tests.
5. Move the remaining callers that need the same policy. Keep callers that
   truly need raw construction separate and name that exception.
6. Restrict the constructor if the language allows it. In TypeScript, make it
   private. In Java, make it private or package-private. In Python, document
   the constructor as internal if access control cannot enforce it.
7. Add a test that proves the factory enforces the policy that motivated the
   refactoring.
8. Add a migration note for public APIs, including the removal version if the
   constructor will be deprecated.

For a large migration, use a compatibility ladder.

1. Add the factory and keep the constructor unchanged.
2. Convert internal call sites first, starting with the highest-risk paths such
   as authentication, billing, parsing, and persistence boundaries.
3. Add a repository search check that reports new constructor calls without
   blocking builds. Let the team see the remaining surface.
4. Turn the report into a blocking check for code owned by the current team.
5. Deprecate the constructor in public docs and examples.
6. Move external integrations and generated code.
7. Restrict or remove the constructor only after telemetry and search show that
   direct construction is gone.

The order matters because the hardest caller is rarely the one in front of the
developer. It is a generated client, a serializer, a test fixture helper, a
plugin, or a script that runs once a month. A compatibility ladder makes those
callers visible before the constructor disappears.

Refactor out when the factory stops earning its place.

1. Count factory routes and constructor routes. If the factory only forwards to
   the constructor and has a vague name, mark it for removal.
2. Inline the factory into direct constructor calls in private code, one group
   at a time.
3. If the factory exists only because of optional parameters, replace it with a
   Builder or Parameter Object rather than reverting to a long constructor.
4. If the factory exists only for a cache that is no longer useful, remove the
   cache first and watch memory and allocation telemetry.
5. For public APIs, deprecate the factory before deletion. Removing a public
   factory can be as breaking as removing a constructor.

Related named refactorings. Introduce Parameter Object prepares long creation
input. Change Function Declaration gives a vague factory a precise name.
Encapsulate Record and Encapsulate Variable protect invariants after creation.
Replace Constructor with Factory Function is often followed by Hide Delegate
when the factory masks an internal representation.

When refactoring out, preserve the caller story. If callers read better with a
factory name even after policy is gone, the factory may still be worthwhile as
domain vocabulary. If the name no longer says anything beyond the type name,
delete it. The test is the same one used to introduce the pattern: does the
creation expression teach a rule?

## 15. Testing and verification

Engineering judgement. Testing should prove the policy, not the existence of a
wrapper.

Test what became easier.

- **Invariant tests.** Feed invalid input to the factory and assert the failure
  mode. Feed valid but messy input and assert the normalized object.
- **Call-site migration tests.** For public APIs, add a search or lint check
  that flags new uses of the deprecated constructor.
- **Return type tests.** When the factory may return a subtype or interface,
  assert behaviour through the public contract rather than checking concrete
  class, except where subtype selection is itself the policy.
- **Cache tests.** When the factory controls identity, assert identity for
  values that should be interned and non-identity for values that should not be
  shared.
- **Error mapping tests.** For Go, Rust, Swift, or TypeScript result-style
  factories, assert that each invalid input maps to the documented error.
- **Fixture tests.** If a test builder or unsafe constructor exists, test that
  production code cannot import it accidentally.

Test what became harder.

- Reflection-heavy tools may skip the factory, so integration tests must cover
  serializers, object mappers, and containers.
- Private constructors can make subclass tests harder. Prefer testing the public
  factory contract unless subclassing is part of the API.
- If the factory hides subtype choice, branch coverage at the factory boundary
  becomes more useful than branch coverage inside callers.

A useful test suite shape has three layers.

The first layer is pure unit tests for the factory. These tests pass ordinary
input and check returned values, errors, and normalized fields. They should be
fast and should not touch databases or networks unless the factory name says it
opens or loads something.

The second layer is contract tests for the object after creation. These tests
do not care which factory route created the object. They assert that every
public operation can rely on the invariants. If several factories create the
same type, run the same contract suite against each route.

The third layer is integration tests for construction tools. Serializers,
dependency injection containers, command-line parsers, and framework binders may
construct objects through reflection or generated code. A factory refactoring is
not complete until those paths either call the factory or validate the object
after construction.

Verification for the examples in this entry. The TypeScript example was
compiled with `npx tsc` and run with `node`. The Python example was run with
`python3`. The Go example was run with `go run`.

## 16. Observability signals

Engineering judgement. A factory function is a useful telemetry boundary
because valid object creation flows through it.

Record these signals when creation policy matters in production.

- A creation counter labelled by factory name and outcome.
- A validation failure counter labelled by reason, with raw private data kept
  out of labels and logs.
- A duration histogram for factories that parse, open, connect, load schema, or
  touch caches.
- A cache hit and miss counter when the factory controls identity.
- A subtype or implementation label when the factory returns an abstraction.
- A deprecated-constructor counter if the constructor still exists during
  migration.

A healthy dashboard shows stable creation volume for each route, low validation
failure rates, and subtype mixes that match release or configuration changes.
Factory duration should be small compared with the operation that uses the
object unless the factory name clearly describes expensive work.

A failing dashboard shows a spike in validation failures after a deploy, which
usually points to a caller that changed input format. It may show deprecated
constructor usage after the migration deadline, which means the public surface
still has a back door. It may show cache hit rate collapse, which points to
normalization drift. It may show one subtype label appearing in an environment
where it should not be built.

Logging should be careful. Factories often receive raw credentials, tokens,
database URLs, personally identifiable data, and untrusted payloads. Log the
policy result and correlation identifier, not the raw constructor arguments.

## 17. Security and privacy implications

Engineering judgement. The refactoring is security-relevant when construction
is the first point where untrusted data becomes a trusted object.

The pattern can reduce attack surface by making invalid states harder to
construct. A factory can normalize usernames, reject malformed URLs, hash
passwords, attach tenant scope, or return a value object whose fields are
already checked. Django's `create_user()` example is security-relevant for this
reason: its documentation ties the helper to password handling and warns
against direct manipulation of the password attribute
(https://docs.djangoproject.com/en/5.2/topics/auth/default/#creating-users,
verified 2026-08-02).

The pattern can also create new risks.

- **Bypass risk.** If the constructor remains public, an attacker or buggy
  internal caller may bypass validation. Close the constructor where possible
  and scan for direct construction.
- **Overtrust risk.** A factory returning an interface can hide an untrusted
  implementation. Validate plugin registrations and avoid accepting factory
  implementations from untrusted packages without sandboxing or review.
- **Secret logging risk.** Creation inputs often contain passwords, tokens,
  keys, or database URLs. Never log raw inputs from a factory by default.
- **Cache retention risk.** Instance-control factories can retain personal data
  longer than the request that created it. Bound caches and define retention
  rules for cached values.
- **Confused deputy risk.** A factory that fills missing tenant, user, or scope
  data from ambient context can accidentally grant access under the wrong
  identity. Prefer explicit context parameters for authorization-sensitive
  creation.
- **Deserialization risk.** Serializers may bypass factories. If invariants are
  security-sensitive, validate after deserialization or configure the tool to
  use the factory.

Where the pattern is silent, say so plainly. A factory function does not encrypt
data, authenticate users, authorize actions, or make mutable objects safe by
itself. It is a place to put creation policy, not a security boundary unless the
constructor cannot be bypassed and the returned object enforces its own
invariants.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Refactoring APIs."
- Martin Fowler, "Replace Constructor with Factory Function,"
  https://refactoring.com/catalog/replaceConstructorWithFactoryFunction.html,
  verified 2026-08-02.
- Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 1,
  "Consider static factory methods instead of constructors."
- Django Software Foundation, "Using the Django authentication system,"
  documentation version 5.2, section "Creating users,"
  https://docs.djangoproject.com/en/5.2/topics/auth/default/#creating-users,
  verified 2026-08-02.
- SQLAlchemy authors, "Engine Configuration," SQLAlchemy 2.0 documentation,
  section `sqlalchemy.create_engine`,
  https://docs.sqlalchemy.org/en/20/core/engines.html, verified 2026-08-02.
- Go authors, "`net/http` package," section `NewRequestWithContext`,
  https://pkg.go.dev/net/http#NewRequestWithContext, verified 2026-08-02.
- Meta Open Source, React API Reference, `createElement`,
  https://react.dev/reference/react/createElement, verified 2026-08-02.
- Oracle, Java SE 21 API documentation, `java.lang.Integer`, method
  `valueOf(int)`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html,
  verified 2026-08-02.
