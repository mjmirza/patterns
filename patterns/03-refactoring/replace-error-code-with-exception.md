---
name: Replace Error Code with Exception
slug: replace-error-code-with-exception
family: 03-refactoring
category: Refactoring
aliases: [Throw Exception Instead of Error Code, Replace Status Return with Exception]
first_described: "Fowler 1999"
maturity: canonical
related: [replace-exception-with-precheck, introduce-assertion, change-function-declaration, separate-query-from-modifier]
incompatible_with: [notification]
verified: 2026-08-02
---

# Replace Error Code with Exception

## 1. Name, aliases, and lineage

The canonical name is **Replace Error Code with Exception**. Martin Fowler
lists the refactoring under that name in the first edition of *Refactoring.
Improving the Design of Existing Code*, Addison-Wesley, 1999, chapter 10,
"Making Method Calls Simpler." Fowler's public catalog also lists **Replace
Error Code with Exception** as a catalog refactoring, with a before and after
summary that moves a returned error value into a thrown exception
(https://refactoring.com/catalog/replaceErrorCodeWithException.html, verified
2026-08-02). Fowler's notes on the second edition list the refactoring as kept
in the new edition and associate the first edition listing with page 310
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

The common aliases are descriptive rather than formal. **Throw Exception Instead
of Error Code** is the phrase many teams use when the old return value is a
negative integer, enum, boolean, or null sentinel. **Replace Status Return with
Exception** is common when the old API returns an object such as `ResultCode`,
`Status`, or `Outcome` and the caller must inspect it after every call.

The lineage is older than the refactoring catalog. C APIs commonly report
failure through integer return codes and expose the reason through a side
channel such as `errno`; Python still documents `errno` as the module that maps
standard system error symbols to integer values
(https://docs.python.org/3/library/errno.html, verified 2026-08-02). Later
language runtimes made exceptions part of ordinary error handling. Java exposes
database failures as `SQLException` objects while still carrying SQLState and a
vendor error code as data on the exception
(https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/SQLException.html,
verified 2026-08-02). Python maps many operating system error numbers into
specific exception classes such as `FileNotFoundError`, `PermissionError`, and
`TimeoutError` (https://docs.python.org/3/library/exceptions.html, verified
2026-08-02). Node.js represents system failures as `Error` objects with stable
`code` and `errno` fields rather than bare return codes
(https://nodejs.org/api/errors.html, verified 2026-08-02). These are not claims
that those libraries performed Fowler's refactoring in one historical change.
They are production examples of the resulting design shape.

This refactoring belongs to the error-handling edge of the refactoring family.
It is not a license to use exceptions for every branch. Fowler separately
discusses moving from exceptions to notifications for validation cases where
the caller expects several ordinary validation messages at once
(https://martinfowler.com/articles/replaceThrowWithNotification.html, verified
2026-08-02). That companion article is the warning label for this entry.

## 2. Problem and context

A function reports failure by returning a value from the same channel it uses to
report success. The caller must remember to inspect that value before it uses
the successful result. If the caller forgets, the program keeps running with a
false assumption.

The common forms are easy to spot.

- `-1`, `0`, or a positive integer means failure, while another integer means a
  valid answer.
- `false` means the operation failed, but the mutated object might already be
  half changed.
- `null` means lookup failed, but the domain might allow null as a real value.
- An enum such as `Status.INVALID_CUSTOMER` is returned while the real output is
  placed into an output parameter, a mutable field, or a caller-owned buffer.
- A tuple such as `(value, errorCode)` is returned, and most callers inspect
  only `value`.

The context that makes the refactoring attractive is a command-like operation
whose normal return value should mean success and whose failure is abnormal for
that call path. The old design forces every caller to repeat the same
conditional check. It also makes nested operations noisy, because each call site
must stop and route the error code by hand.

Consider a payment authorization function. In the old design,
`reserve(amount)` returns `0` for success, `1` for insufficient funds, and `2`
for a frozen account. A checkout workflow then calls `reserve`, `recordOrder`,
`sendReceipt`, and `enqueueFulfillment`. Every step now mixes the business
path with repeated `if code != 0` checks. A missed check lets the order advance
after the reservation failed. The status value was meant to protect the
workflow, but it became a value the workflow could ignore.

After the refactoring, `reserve(amount)` returns normally only when the money is
reserved. Insufficient funds and frozen accounts become exception classes or
exception variants. The checkout workflow can read as a success path, and the
error policy sits at the boundary that can respond, such as the request handler,
job runner, or transaction wrapper.

This refactoring is strongest when it repairs a broken contract. The contract
becomes: this function either completes the named action or throws. That
contract is clearer than: this function might return a value that asks you to
decide whether the action happened.

## 3. Forces

This dimension is engineering judgement, except where a named runtime or API is
cited.

- **Correctness.** Favoured. A missed error-code check is one of the easiest
  bugs to write and one of the hardest to notice in review. An uncaught
  exception makes the failure visible by leaving the current control path.
- **Local readability.** Favoured for callers on the success path. The normal
  path no longer pays a conditional after every call.
- **Control-flow explicitness.** Sacrificed. A return statement is visible in
  the called function and a branch is visible in the caller. Exception
  propagation crosses stack frames, so the reader must know where the nearest
  handler lives.
- **Coupling.** Favoured when callers catch a small exception hierarchy rather
  than compare numeric constants. Sacrificed if callers start catching concrete
  exception classes from deep infrastructure packages.
- **Consistency.** Favoured when many functions in the same module move to the
  same rule: success returns normally, failure throws. Sacrificed during a
  migration period where some functions return codes and neighboring functions
  throw.
- **Latency.** Neutral for the success path in many modern runtimes, but
  sacrificed on the failure path because constructing and propagating an
  exception often records type, message, and stack information. Swift documents
  its error model as having performance characteristics comparable to return
  statements, while also saying it differs from exception handling in many
  languages (https://docs.swift.org/swift-book/LanguageGuide/ErrorHandling.html,
  verified 2026-08-02). That Swift statement should not be generalized to Java,
  Python, JavaScript, or other runtimes.
- **Operability.** Favoured when exceptions carry type, message, cause, and
  structured fields. Sacrificed when catch blocks flatten everything into a
  vague log line.
- **Cost of change.** Sacrificed at published API boundaries. Changing a return
  code into a thrown exception is a breaking contract change for callers.
- **Team topology.** Favoured inside one service or one library owned by one
  team. Sacrificed across many client teams because every caller must migrate in
  a coordinated window.
- **Cognitive load.** Favoured once the local convention is uniform. Sacrificed
  where the language has checked exceptions, implicit exception propagation, or
  mixed idioms that make the handler hard to predict.

The refactoring pays for itself when missed checks are a real risk and failures
should abort the current operation. It does not pay for itself when the failure
is an expected answer the caller will branch on as part of ordinary control
flow.

## 4. Applicability and non-applicability

Reach for Replace Error Code with Exception when the following hold.

- A method returns a special value that means failure, and callers often forget
  or inconsistently perform the check.
- The operation is command-like. A normal return means the action happened, and
  failure means the action did not happen.
- The caller cannot repair the failure locally at every call site. The decision
  belongs at a higher boundary such as an HTTP handler, message consumer, CLI
  entry point, scheduler, or transaction wrapper.
- The error carries context that belongs with the failure, such as the account
  id, field name, path, SQLState, remote endpoint, retry policy, or underlying
  cause.
- A constructor or initializer needs to report failure. Constructors cannot
  return a status code in many object-oriented languages, while throwing
  initializers or constructors can report invalid construction.
- A series of calls must abort on the first failure. Exception propagation keeps
  the chain from repeating the same branch after each call.
- Existing callers already convert the code into an exception at their boundary.
  Moving the throw nearer to the failing operation removes duplicated adapter
  code.

Do NOT reach for this refactoring in these non-applicability cases.

- **The condition is an expected business answer.** A search that finds no row,
  a username that is already taken, or a validation field that is missing may be
  normal in the workflow. Return an option, result object, notification, or
  validation report.
- **The caller must collect multiple problems.** Throwing on the first invalid
  field prevents the caller from returning a complete validation report. Use a
  Notification object or a list of violations. Fowler's validation article makes
  this distinction for cases where several validation messages are useful
  (https://martinfowler.com/articles/replaceThrowWithNotification.html,
  verified 2026-08-02).
- **The language community uses typed result values for recoverable errors.**
  In Go, the idiom is to return a value plus an `error`, and the standard
  library is built around that convention. Replacing all such returns with
  panics would fight the language. Use the refactoring only at a boundary where
  a panic or exception is idiomatic for that framework.
- **The API is a stable external contract.** A public function changing from
  `Status` to a thrown exception breaks callers. Add a new throwing API and keep
  an adapter until clients migrate.
- **The old code is a protocol value, not a programming interface smell.** HTTP
  status codes, POSIX errno values, SQLState strings, and payment processor
  decline codes are interoperable data. Keep them as data and wrap them in an
  exception object only inside your language boundary.
- **The failure path is hot and expected.** A parser that rejects millions of
  tokens per second should not throw for each mismatch. Use a result value or a
  recognizer that reports match or no match cheaply.
- **The caller has a useful local fallback at most call sites.** If each caller
  naturally branches to a different fallback, an exception may hide the decision
  rather than clarify it.
- **The system crosses process boundaries.** Exceptions do not travel over HTTP,
  queues, files, or RPC as language exceptions. Convert to an error response,
  event, or status envelope at the boundary.
- **The code currently returns several independent warning codes with success.**
  Exceptions model failure, not "success with warnings." Use a result object
  that can carry value plus warnings.
- **The language lacks exception handling or bans it by policy.** Embedded C,
  kernel code, and some high-reliability C++ profiles avoid exceptions. Use a
  typed result, error object, or explicit status channel.

## 5. Structure

The refactoring has six participants.

- **Failing operation.** The function or method currently returning the error
  code. After the refactoring it returns only the success value, or returns
  nothing when the operation is a command.
- **Error code.** The sentinel value, enum member, boolean, null, or status
  object that means failure. During the refactoring each code is mapped to an
  exception type, an exception variant, or structured fields on one exception.
- **Domain exception.** The new thrown value. It names the failure in domain
  language and carries the old code when that code remains useful for logging,
  interoperability, or downstream matching.
- **Local caller.** A caller near the failing operation. After the refactoring
  it stops checking the old return code and either lets the exception propagate
  or catches only the cases it can repair.
- **Boundary handler.** The layer that converts exceptions into process-visible
  outcomes, such as HTTP responses, CLI exit statuses, rejected promises, log
  events, or retry decisions.
- **Compatibility adapter.** A temporary wrapper for published APIs. It calls
  the throwing operation and converts known exceptions back to the old code for
  callers that have not migrated.

The relationship change is small but deep. Before the refactoring, every caller
must know the error-code vocabulary and remember to branch. After the
refactoring, the failing operation owns the decision to throw, local callers
own only recoverable cases, and the boundary handler owns translation to the
outside world.

## 6. ASCII structure diagram

```
  BEFORE

  +-------------------+       returns value or code       +-------------+
  | FailingOperation  |----------------------------------->| LocalCaller |
  |-------------------|                                    |-------------|
  | + reserve(): int  |                                    | if code != 0|
  +-------------------+                                    +-------------+
           |                                                       |
           | many callers repeat the same test                     |
           v                                                       v
  +-------------------+                                    +-------------+
  | ErrorCode enum    |                                    | MoreCallers |
  | OK, NO_FUNDS, ... |                                    | if code != 0|
  +-------------------+                                    +-------------+


  AFTER

  +-------------------+       returns on success only      +-------------+
  | FailingOperation  |----------------------------------->| LocalCaller |
  |-------------------|                                    |-------------|
  | + reserve(): void |                                    | no status if|
  |   throws DomainEx |                                    +-------------+
  +-------------------+                                            |
           | throws                                                |
           v                                                       v
  +-------------------+       handled or translated        +-------------+
  | DomainException   |----------------------------------->| Boundary    |
  | type, code, cause |                                    | Handler     |
  +-------------------+                                    +-------------+
```

## 7. Dynamics

The runtime change is that failure exits the local call path without each
intermediate caller returning and checking a code. The success path becomes a
straight line. The failure path is routed by the runtime's exception mechanism
until a handler catches it.

```
  SUCCESS PATH

  RequestHandler       Checkout        Ledger
       |                  |              |
       | reserve()        |              |
       |----------------->|              |
       |                  | debit()      |
       |                  |------------->|
       |                  |<-------------|
       |<-----------------|              |
       | render 201       |              |


  FAILURE PATH AFTER THE REFACTORING

  RequestHandler       Checkout        Ledger
       |                  |              |
       | reserve()        |              |
       |----------------->|              |
       |                  | debit()      |
       |                  |------------->|
       |                  | throws NoFunds
       |                  |<-------------|
       | exception propagates            |
       |<-----------------|              |
       | catch NoFunds                   |
       | render 402                     |


  FAILURE PATH BEFORE THE REFACTORING

  RequestHandler       Checkout        Ledger
       |                  |              |
       | reserve()        |              |
       |----------------->|              |
       |                  | debit()      |
       |                  |------------->|
       |                  | return NO_FUNDS
       |                  |<-------------|
       |                  | if code != OK|
       | return NO_FUNDS  |              |
       |<-----------------|              |
       | if code != OK                   |
       | render 402                     |
```

Two runtime rules follow.

First, catch where a policy decision exists. A lower-level function that catches
an exception and returns a different status code often recreates the old design
with extra syntax. Second, preserve the original code as data when an external
system supplied it. For example, a database exception can expose SQLState and a
vendor code while still using exception propagation inside Java's API
(https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/SQLException.html,
verified 2026-08-02).

## 8. Implementation variants

**One exception class per error code.** Each previous code becomes a named
exception class, such as `InsufficientFunds` or `FrozenAccount`. This makes
catch clauses readable and lets different handlers catch different categories.
The cost is type count. Use this when each failure has a distinct response or
distinct fields.

**One exception class with a code field.** The old code becomes a field on a
single exception, such as `PaymentError(code="NO_FUNDS")`. This preserves the
old vocabulary while moving propagation to exceptions. It fits APIs that must
log or expose a vendor code. Java's `SQLException` is a production example of
an exception object that carries SQLState and vendor code
(https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/SQLException.html,
verified 2026-08-02).

**Exception hierarchy.** Low-level exceptions inherit from a broader domain
exception. Callers that can repair a case catch the specific subtype, and
boundary handlers catch the broader type. Requests documents a hierarchy where
explicitly raised exceptions inherit from `RequestException`
(https://requests.readthedocs.io/en/latest/user/quickstart/, verified
2026-08-02). The same shape works for application domains.

**Typed enum error.** Swift models errors as values whose types conform to the
`Error` protocol, and enumerations are shown in the Swift language guide as a
natural way to model related error conditions
(https://docs.swift.org/swift-book/LanguageGuide/ErrorHandling.html, verified
2026-08-02). This variant keeps the error set compact and pattern-matchable.

**Exception wrapping.** The new domain exception carries the original exception
as a cause. Node.js documents `error.cause` as a way to retain an underlying
cause when throwing a new error with different message or code
(https://nodejs.org/dist/latest/docs/api/errors.html, verified 2026-08-02).
Use this when translating infrastructure failures into domain language.

**Compatibility wrapper.** Keep the old function name returning the old status
and add a new throwing function, or invert that relationship depending on the
published contract. The old wrapper catches known exceptions and maps them back
to codes. Delete it after clients migrate.

**Result type instead of exception.** In languages or modules where recoverable
failure is expected, the refactoring may stop at a typed result such as
`Result<T, E>` rather than an exception. This is not Fowler's refactoring, but
it is often the right design. Judgement: pick it when callers commonly branch
on the failure as ordinary business logic.

**Async exception or rejected promise.** In JavaScript and TypeScript, a
throwing `async` function rejects the returned promise. The caller observes the
failure with `await` inside `try` and `catch`, or with promise rejection
handling. The same design rule applies: return normally only for success, reject
for abnormal failure.

## 9. Known production uses

**Java JDBC, `SQLException`.** JDBC APIs report database access failures through
`SQLException`. The exception object carries a reason, SQLState, vendor-specific
error code, chained exceptions, and cause according to the Java SE 21 API
documentation
(https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/SQLException.html,
verified 2026-08-02). This is the target shape of the refactoring: code-based
database failure information becomes data on a thrown object.

**Python standard library, `OSError` subclasses.** Python documents `OSError` as
raised for system-related errors, and documents subclasses that correspond to
specific `errno` values, including `FileNotFoundError` for `ENOENT`,
`PermissionError` for `EACCES` and `EPERM`, and `TimeoutError` for `ETIMEDOUT`
(https://docs.python.org/3/library/exceptions.html, verified 2026-08-02). The
separate `errno` module documents the integer symbols and mapping names
(https://docs.python.org/3/library/errno.html, verified 2026-08-02). This is a
production design where operating system codes are exposed through exception
types and fields rather than through a plain integer return from Python APIs.

**Node.js runtime, system errors.** Node.js documentation says system errors are
represented as `Error` objects with fields such as `code`, `errno`, `path`, and
`syscall`; it also states that JavaScript errors are handled as exceptions using
the language `throw` mechanism (https://nodejs.org/api/errors.html, verified
2026-08-02). This is a production use of exceptions that still preserves stable
code fields for programmatic handling.

**Requests for Python, exception hierarchy.** Requests documents that network
problems raise `ConnectionError`, unsuccessful HTTP status handling through
`raise_for_status()` raises `HTTPError`, timeouts raise `Timeout`, and the
explicit exceptions inherit from `RequestException`
(https://requests.readthedocs.io/en/latest/user/quickstart/, verified
2026-08-02). Its API reference also documents `raise_for_status()` as raising
`HTTPError` when one occurred
(https://docs.python-requests.org/en/latest/api/?highlight=raise_for_status,
verified 2026-08-02). This is the common boundary form: a response object may
carry status data, while callers that opt into exception handling can convert
unsuccessful statuses into thrown errors.

**Django, `Http404`.** Django documents that raising `Http404` inside a view
causes Django to load the 404 handling view
(https://docs.djangoproject.com/en/6.0/ref/views/, verified 2026-08-02). This
is a web framework example where application code can throw a domain-level
exception and the boundary handler translates it into an HTTP response.

## 10. Consequences

Positive.

- The success path reads as the work being done, not as repeated status checks.
- A missed failure check becomes harder to hide. If no handler exists, the
  failure escapes instead of being treated as a successful value.
- Error context can travel with the failure in fields, message, type, cause,
  and stack trace.
- Intermediate functions no longer need to translate or forward the same status
  code by hand.
- Constructors and initialization logic gain a natural failure channel in
  languages where returning a status from construction is unavailable.
- Boundary handlers can centralize translation from domain failures to HTTP
  responses, exit codes, retry behavior, or audit events.
- A small exception hierarchy creates a vocabulary for failures that is easier
  to read than numeric constants.

Negative.

- Exception propagation is less local than a returned value. A reader must find
  the nearest handler to know the policy.
- Published APIs break when callers were written to inspect return codes.
- Overbroad catch blocks can hide defects and convert unrelated failures into
  the wrong response.
- Exceptions can be expensive on a hot failure path, depending on runtime and
  stack capture behavior.
- A large exception hierarchy can become another taxonomy that developers must
  memorize.
- Mixed styles during migration are confusing. Neighboring functions can signal
  failure in incompatible ways.
- Exception objects can leak private context through messages, stack traces, or
  serialized fields if the boundary handler exposes them.

Judgement: the benefit is highest where error-code checks are duplicated and
often missed. The cost is highest where failure is frequent, expected, and
locally handled.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Symptom.** Logs show `Exception` or `Error` caught at a broad boundary and the
client receives the same generic response for every failure. **Cause.** The
refactoring replaced numeric codes with one vague exception and no structured
fields. **Fix.** Introduce named exception subtypes or a stable `code` field,
and map each handled case at the boundary.

**Symptom.** A checkout, import, or batch job continues after a failure even
though the failing function now throws. **Cause.** A local catch block swallowed
the exception and returned success to preserve an old method signature. **Fix.**
Move handling to the policy boundary, or return a typed result that represents
partial success honestly.

**Symptom.** Callers contain `try` and `catch` after almost every line, with
logic no shorter than the old code checks. **Cause.** Exceptions were added
where each caller has a different local recovery path. **Fix.** Use a result
object, option, or notification for expected answers, and reserve exceptions for
failures that abort the current operation.

**Symptom.** Alert volume rises because common validation failures now log full
stack traces. **Cause.** User input validation was modeled as exceptional
failure. **Fix.** Replace the exception with a validation report or
Notification object, and log validation failures as product metrics rather than
errors.

**Symptom.** A public client library release causes downstream compile failures
or uncaught runtime failures. **Cause.** The return contract changed without a
compatibility adapter or migration window. **Fix.** Add a new throwing API,
leave the old status-returning API as a wrapper, publish migration notes, and
remove the old API in a later major version.

**Symptom.** A handler catches `Throwable`, `BaseException`, or a top-level
`Exception` class and retries forever. **Cause.** The catch block groups
programmer bugs, cancellation, and recoverable domain failures together. **Fix.**
Catch only the domain exception hierarchy that the operation documents, and let
programmer errors and cancellation propagate according to platform policy.

**Symptom.** Security reports show database names, filesystem paths, tokens, or
internal URLs in client-facing error bodies. **Cause.** Exception messages were
serialized directly after the refactoring. **Fix.** Separate internal exception
data from public error responses, redact fields at the boundary, and assign a
public error code for clients.

**Symptom.** A batch processor loses the original vendor code needed for support
triage. **Cause.** The refactoring threw a domain exception but discarded the
old code. **Fix.** Carry the old code as a structured field or cause, and add a
test that checks the mapping.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Error Code with Exception | Return Result or Either | Notification | Null Object | Introduce Assertion | Error Callback |
|---|---|---|---|---|---|---|
| Correctness when caller forgets | High. Failure leaves path | Medium. Caller can ignore | Medium. Caller can ignore | Medium. No failure, but may mask cause | High for programmer errors | Medium. Callback can be omitted |
| Success-path readability | High | Medium. Unwrap needed | Medium. Report checked later | High | High | Low. Callback noise |
| Control-flow explicitness | Medium. Handler may be far away | High. Value is visible | High. Report is visible | High | Medium. Assertion aborts | Medium |
| Expected business failure | Poor | Good | Strong for many messages | Good for missing behavior | Poor | Medium |
| Multiple validation errors | Poor | Medium | Strong | Poor | Poor | Medium |
| Hot failure path | Runtime dependent, often poor | Good | Good | Good | Good if disabled or cheap | Good |
| API compatibility | Breaking unless wrapped | Breaking if return type changes | Breaking if return type changes | Medium | Usually internal | Medium |
| Boundary translation | Strong | Medium | Medium | Weak | Weak | Medium |
| Carries diagnostic context | Strong if designed | Strong | Strong | Weak | Medium | Medium |
| Team migration cost | Medium to high | Medium | Medium | Low to medium | Low | Medium |

Reading of the table. Replace Error Code with Exception wins when failure
should abort the current operation and one boundary owns the response policy.
Return Result wins where callers branch locally. Notification wins where the
caller wants all validation messages. Null Object wins only when absence can
behave like a real object. Introduce Assertion wins for programmer mistakes,
not runtime failures. Error Callback fits event-driven APIs, but it can scatter
policy across callbacks.

## 13. Related and incompatible patterns

- **Replace Exception with Precheck.** The inverse direction. If callers can
  cheaply test a condition before calling, and the condition is expected, a
  precheck can remove exception-driven control flow.
- **Introduce Assertion.** Related but narrower. Assertions state programmer
  assumptions and often fail in development or test. This refactoring models
  recoverable runtime failures that need a handler.
- **Notification.** Often incompatible. A Notification gathers many validation
  problems and returns them as data. Throwing an exception on the first problem
  blocks that use case.
- **Null Object.** A substitute when the old error code means absence and there
  is a harmless behavior for absence. It is a poor substitute when the caller
  must know why the operation failed.
- **Result or Either.** A substitute in functional code and in languages where
  recoverable failure is modeled as data. It keeps control flow explicit but
  leaves caller discipline in place.
- **Special Case.** Related when a specific missing or exceptional domain value
  can be represented by an object with domain behavior. Use it when the caller
  should continue, not when the operation must abort.
- **Change Function Declaration.** Often required during migration, because a
  method that used to return a status may need a new return type, a new name, or
  documentation of thrown failures.
- **Separate Query from Modifier.** Helpful before this refactoring. If a method
  both mutates state and returns a status, split the query from the command so
  failure semantics are easier to reason about.
- **Circuit Breaker.** Composes at a service boundary. Exceptions from remote
  failures are often the signal a circuit breaker counts, while the breaker
  decides whether to allow more calls.

## 14. Refactoring path in and out

Introduce the refactoring one error code at a time.

1. Identify the function that returns the error code and list every caller. Use
   search, not memory. A missed caller is the most common migration bug.
2. Classify each code. Mark codes that are true failures, expected business
   answers, warnings, and success values. Only true failures move to exceptions.
3. Create the exception type or exception hierarchy. Preserve the old code as a
   field when logs, support tools, or external protocols still need it.
4. Add tests around the current behavior. Cover success, each failure code, and
   at least one caller that forgets no check after migration.
5. Add a throwing implementation behind the old function, or add a new throwing
   function beside it. Keep the old public function as a compatibility adapter
   if any external caller depends on the status return.
6. Migrate callers from nearest to farthest. Local callers should stop checking
   the old status and either let the exception propagate or catch a named
   failure they can repair.
7. Add or update the boundary handler. Translate domain exceptions to HTTP
   responses, CLI exit statuses, job retry decisions, or user-visible messages.
8. Remove obsolete status checks after the last caller migrates. Dead checks are
   risky because they suggest a failure path that can no longer happen.
9. Delete the compatibility adapter only when the API migration window closes.

Refactor out when exceptions stop earning their place.

1. Count catch sites. If almost every caller catches the same exception next to
   the call, the failure is part of ordinary control flow.
2. Introduce a typed result or notification beside the throwing API.
3. Change local catch blocks into result handling at the call site.
4. Keep one adapter that throws for legacy callers that still prefer exception
   propagation.
5. Move boundary mapping from exception type to result code.
6. Delete exception types that no longer cross a meaningful boundary.

Judgement: the safest migration is not "flip the callee and fix the compiler."
It is "add the throwing shape, migrate callers, then remove the old shape."
That order keeps production behavior understandable between commits.

## 15. Testing and verification

This dimension is engineering judgement.

Tests before the refactoring should freeze behavior without freezing the old
interface forever. Write characterization tests that prove each old code maps to
the intended response. Then write new tests against the exception contract.

Useful tests.

- **Success contract test.** The function returns the success value or mutates
  state only when no exception is thrown.
- **Exception mapping test.** Each old error code maps to the intended exception
  type and structured fields. If the old code must survive for logging, assert
  the field value.
- **Boundary translation test.** The HTTP handler, CLI command, job runner, or
  queue consumer converts the exception to the correct external result.
- **Propagation test.** An intermediate caller that has no recovery policy does
  not catch and translate the exception.
- **Compatibility adapter test.** The old API catches the new exception and
  returns the old code until the adapter is removed.
- **Cause preservation test.** Wrapped infrastructure exceptions keep their
  cause so support tooling can find the root failure.
- **Redaction test.** Public responses derived from exceptions do not expose
  private paths, tokens, SQL text, or stack traces.

What gets easier. The success path is easier to test because a normal return
means success. Tests no longer need to assert both a value and a status code
after each call. Boundary tests become cleaner because one handler can be fed a
domain exception and checked for one response.

What gets harder. Static analysis of all possible thrown failures can be weak in
languages without checked exceptions or typed throws. Tests must cover the
exception taxonomy and boundary mapping because the compiler may not. Async code
also needs tests for rejected promises or failed tasks; a test that forgets to
await can miss the failure.

Verification techniques.

- Inject a fake lower-level dependency that throws each domain exception, then
  assert the caller either propagates it or translates it correctly.
- Use mutation testing or a targeted test edit to remove a catch block and check
  that a boundary test fails.
- In Java, compile checked exception examples so signature changes are real, not
  comments.
- In Python and TypeScript, assert exception class and fields rather than string
  messages alone. Messages change more often than codes or classes.
- In JavaScript and TypeScript, test both sync throws and rejected promises with
  `await expect(...).rejects` or equivalent local test helpers.

## 16. Observability signals

This dimension is engineering judgement.

The refactoring moves failure from ordinary return values into exceptional
control flow. Production telemetry must make that path visible.

Record these signals.

- A counter for thrown domain exceptions, labeled by exception class or stable
  code.
- A counter for boundary translations, labeled by external status such as HTTP
  status, CLI exit code, job retry, or dead-letter reason.
- A histogram for operation duration split by success and exception class.
- A structured log event at the boundary with correlation id, exception class,
  stable code, redacted message, and cause class.
- A metric for compatibility adapter use. It should trend to zero during
  migration.
- A metric for unknown exception mappings at each boundary. It should be zero
  outside new deployments.
- A sampled stack trace for unexpected exception classes, with private values
  redacted before export.

A healthy instance shows a stable exception distribution that matches product
activity. For example, a public API may show some `NotFound` and `Unauthorized`
domain exceptions, few `Conflict` exceptions, and near-zero unknown mappings.
Adapter-use metrics decline as callers migrate. Boundary translations match the
same counts as thrown domain exceptions after accounting for retries.

A failing instance shows one of four shapes. First, unknown exception mappings
rise after a deploy, meaning a new exception type lacks boundary policy. Second,
one exception class spikes with no matching product event, meaning a dependency
or validation rule changed. Third, adapter use stays flat, meaning clients did
not migrate. Fourth, the same exception appears at multiple boundaries with
different external statuses, meaning policy is duplicated and inconsistent.

Log at the boundary, not at every throw site. Logging at every throw site and at
the handler creates duplicate incidents for one failure. The throw site should
attach context to the exception. The handler should record the operational
event.

## 17. Security and privacy implications

This dimension is engineering judgement, with cited examples limited to API
contracts.

The refactoring can improve security when it prevents ignored failures. A failed
authorization, failed audit write, failed quota check, or failed policy lookup
must not be a return code that a caller can forget to inspect. Throwing forces
the current operation off the success path unless a handler chooses a policy.

It can also create new exposure.

- **Information disclosure.** Exception messages and stack traces often contain
  paths, SQL fragments, identifiers, or endpoint names. Boundary handlers must
  convert internal exceptions into public responses with stable public codes and
  redacted messages.
- **Overbroad recovery.** Catching a broad base exception can convert security
  failures into success or retry loops. Catch the domain failures the boundary
  owns and let other failures follow platform policy.
- **Cause leakage.** Wrapping lower-level failures is good for diagnosis, but
  the cause chain should stay inside logs and traces. Do not serialize full
  causes to untrusted clients.
- **Protocol confusion.** External status codes remain protocol data. HTTP
  status, SQLState, POSIX errno, and vendor decline codes should not disappear.
  They should be carried in structured exception fields or boundary responses
  where the protocol requires them.
- **Denial of service through stack capture.** A common invalid input that
  throws and logs a stack trace on every request can create CPU, memory, and log
  pressure. Model expected invalid input as validation data and rate-limit logs
  at the boundary.

Privacy guidance. Treat exception objects as internal data. Give them fields
that support operators and developers, then map them to public error objects
with a smaller field set. Test that mapping. The more context an exception
carries, the more disciplined the boundary must be.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 10, "Making Method Calls Simpler,"
  Replace Error Code with Exception.
- Martin Fowler, "Replace Error Code with Exception," refactoring catalog,
  https://refactoring.com/catalog/replaceErrorCodeWithException.html, verified
  2026-08-02.
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Martin Fowler, "Refactoring,"
  https://www.martinfowler.com/books/refactoring.html, verified 2026-08-02.
- Martin Fowler, "Replacing Throwing Exceptions with Notification in
  Validations,"
  https://martinfowler.com/articles/replaceThrowWithNotification.html, verified
  2026-08-02.
- Oracle, Java SE 21 API documentation, `java.sql.SQLException`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/SQLException.html,
  verified 2026-08-02.
- Python Software Foundation, Python 3 documentation, `errno`,
  https://docs.python.org/3/library/errno.html, verified 2026-08-02.
- Python Software Foundation, Python 3 documentation, built-in exceptions,
  https://docs.python.org/3/library/exceptions.html, verified 2026-08-02.
- OpenJS Foundation, Node.js API documentation, Errors,
  https://nodejs.org/api/errors.html, verified 2026-08-02.
- OpenJS Foundation, Node.js API documentation, Errors,
  https://nodejs.org/dist/latest/docs/api/errors.html, verified 2026-08-02.
- Requests project, Requests documentation, Quickstart, Errors and Exceptions,
  https://requests.readthedocs.io/en/latest/user/quickstart/, verified
  2026-08-02.
- Requests project, Requests API documentation, `Response.raise_for_status`,
  https://docs.python-requests.org/en/latest/api/?highlight=raise_for_status,
  verified 2026-08-02.
- Django Software Foundation, Django documentation, built-in views, 404 view,
  https://docs.djangoproject.com/en/6.0/ref/views/, verified 2026-08-02.
- The Swift Programming Language, Error Handling,
  https://docs.swift.org/swift-book/LanguageGuide/ErrorHandling.html, verified
  2026-08-02.

## Code examples

The examples use TypeScript, Python, and Swift because those languages support
ordinary throwing APIs and are available in this repository's toolchain. Go and
Rust are omitted because their idiomatic recoverable-error style is a typed
return value, so replacing recoverable error returns with exceptions would fight
the language.

```typescript
class PaymentError extends Error {
  constructor(
    readonly code: "NO_FUNDS" | "FROZEN_ACCOUNT",
    readonly accountId: string,
  ) {
    super(`${code} for account ${accountId}`);
    this.name = "PaymentError";
  }
}

class Account {
  constructor(
    readonly id: string,
    private balance: number,
    private frozen = false,
  ) {}

  reserve(amount: number): void {
    if (this.frozen) {
      throw new PaymentError("FROZEN_ACCOUNT", this.id);
    }
    if (amount > this.balance) {
      throw new PaymentError("NO_FUNDS", this.id);
    }
    this.balance -= amount;
  }
}

function checkout(account: Account, amount: number): string {
  try {
    account.reserve(amount);
    return "reserved";
  } catch (error) {
    if (error instanceof PaymentError && error.code === "NO_FUNDS") {
      return "ask for another card";
    }
    throw error;
  }
}

console.log(checkout(new Account("acct-1", 10), 25));
console.log(checkout(new Account("acct-2", 40), 25));
```

```python
class PaymentError(Exception):
    def __init__(self, code: str, account_id: str) -> None:
        super().__init__(f"{code} for account {account_id}")
        self.code = code
        self.account_id = account_id


class Account:
    def __init__(self, account_id: str, balance: int, frozen: bool = False) -> None:
        self.account_id = account_id
        self.balance = balance
        self.frozen = frozen

    def reserve(self, amount: int) -> None:
        if self.frozen:
            raise PaymentError("FROZEN_ACCOUNT", self.account_id)
        if amount > self.balance:
            raise PaymentError("NO_FUNDS", self.account_id)
        self.balance -= amount


def checkout(account: Account, amount: int) -> str:
    try:
        account.reserve(amount)
        return "reserved"
    except PaymentError as error:
        if error.code == "NO_FUNDS":
            return "ask for another card"
        raise


print(checkout(Account("acct-1", 10), 25))
print(checkout(Account("acct-2", 40), 25))
```

```swift
enum PaymentError: Error {
    case noFunds(accountId: String)
    case frozenAccount(accountId: String)
}

final class Account {
    let id: String
    private var balance: Int
    private let frozen: Bool

    init(id: String, balance: Int, frozen: Bool = false) {
        self.id = id
        self.balance = balance
        self.frozen = frozen
    }

    func reserve(_ amount: Int) throws {
        if frozen {
            throw PaymentError.frozenAccount(accountId: id)
        }
        if amount > balance {
            throw PaymentError.noFunds(accountId: id)
        }
        balance -= amount
    }
}

func checkout(_ account: Account, amount: Int) throws -> String {
    do {
        try account.reserve(amount)
        return "reserved"
    } catch PaymentError.noFunds {
        return "ask for another card"
    }
}

print(try checkout(Account(id: "acct-1", balance: 10), amount: 25))
print(try checkout(Account(id: "acct-2", balance: 40), amount: 25))
```
