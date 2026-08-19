---
name: Introduce Assertion
slug: introduce-assertion
family: 03-refactoring
category: Refactoring
aliases: [Add Precondition, Assert Invariant, Explicit Assumption]
first_described: "Fowler 1999"
maturity: canonical
related: [replace-exception-with-test, replace-assertion-with-test, encapsulate-variable, extract-function, replace-constructor-with-factory-function]
incompatible_with: []
verified: 2026-08-13
---

# Introduce Assertion

## 1. Name, aliases, and lineage

The canonical name is **Introduce Assertion**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 10, "Making Method Calls Simpler." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 11, "Making Calls Simpler," under the same name and with the same
mechanics.

The underlying idea, that an assumption the code depends on should be
stated explicitly so a violation is caught at the point of the assumption
rather than at the point where it produces wrong behaviour, goes back to
the design by contract methodology of Bertrand Meyer, *Object-Oriented
Software Construction*, Prentice Hall, 1988, which introduced preconditions,
postconditions, and invariants as executable assertions. The Eiffel
programming language implements these as first class language constructs.

The term **assertion** in the programming sense was popularised by C.A.R.
Hoare, "Assertions: A Personal Perspective," 1973, and the ANSI C
standard's `assert` macro, introduced in C89, made runtime assertions a
standard library feature. Fowler's refactoring brings the practice from
the language and methodology communities into the refactoring catalog.

The alias **Add Precondition** is used in the design by contract community,
where an assertion at the start of a function is a precondition. The alias
**Assert Invariant** is used in the immutable data community, where an
assertion that a condition holds after construction is an invariant check.

## 2. Problem and context

A section of code makes an assumption about the state of the program at
that point, for example that a divisor is not zero, that a list is not
empty, or that a temperature is in a valid range. The assumption is not
checked, because the author believed the callers would always provide
valid inputs. When a caller provides an invalid input, the assumption is
violated silently, and the code produces wrong behaviour or a confusing
error far from the point where the assumption was made.

The situation reads like this. A function `calculateSpeed` takes a
`distance` and a `time` and returns `distance / time`. The function
assumes `time` is not zero, but it does not check. When a caller passes
`time = 0`, the function divides by zero, which in Python raises a
`ZeroDivisionError` and in Java produces `Infinity` or a
`ArithmeticException`. The error is caught, but the message says "division
by zero" with no context about which calculation or which caller
produced the invalid input. The root cause is a time of zero, but the
error appears at the division, not at the point where the zero was
passed.

The fix is to introduce an assertion. At the start of the function, add
`assert time != 0, "time must be non-zero"`. If a caller passes zero, the
assertion fires with a message that names the assumption and the
function, and the error is caught at the point where the assumption was
made, not at the point where the division produced a confusing result.

## 3. Forces

**Fail fast versus error handling.** An assertion fails fast, catching a
programming error at the point of the assumption. Error handling,
such as a try catch block, catches the error later when it produces a
symptom. The force favours assertions when the error is a programming
mistake that should be fixed, not handled at runtime.

**Documentation versus execution.** A comment can state the assumption
without executing a check, which is documentation but not enforcement. An
assertion is both documentation and enforcement, because it executes and
fails if the assumption is violated. The force favours assertions over
comments when the assumption is load bearing and a violation would
produce a confusing error.

**Debug versus production.** In many languages, assertions are disabled
in production, which means they catch errors only in development and
testing. The force favours assertions for programming errors that should
be caught in development, and favours explicit checks for conditions
that can occur in production.

**Performance versus safety.** An assertion adds a check on every
execution, which has a cost. In debug builds the cost is accepted, in
production builds the assertion is typically stripped. The force favours
assertions when the check is cheap and the error is a programming mistake,
and favours no check when the check is expensive and the error is
unlikely.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The code makes an assumption about the state of the program that is
  not checked, and a violation would produce a confusing error or wrong
  behaviour far from the root cause.
- The assumption is a precondition that the caller must satisfy, not a
  condition that can legitimately occur at runtime. The assertion catches
  a programming error, not a runtime condition.
- The check is cheap, so the assertion does not add measurable cost in
  development.
- The assertion message would help a developer diagnose the root cause,
  which means it names the assumption and the function.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The condition can legitimately occur at runtime, for example a file not
  found or a network timeout. An assertion would crash the program for a
  condition that error handling should recover from.
- The check is expensive, for example checking that a list is sorted, and
  the cost is unacceptable even in development.
- The language does not have assertions, and the alternative is an if
  statement that throws, which is Replace Exception with Test, not
  Introduce Assertion.
- The assertion would be disabled in production, and the condition must
  be checked in production. An explicit if check is the right approach,
  not an assertion.

## 5. Structure

The refactoring has one participant.

- **The assumption.** A condition the code depends on. After the
  refactoring, the condition is checked with an assertion at the point
  where the code depends on it.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  def calculate(distance, time):      def calculate(distance, time):
      return distance / time              assert time != 0, "time must be non-zero"
                                          return distance / time

  (no check, assumption implicit)     (assertion makes assumption explicit)
```

## 7. Dynamics

```
  t0  identify assumption the code depends on
       |
       v
  t1  determine the condition that must hold
       |
       v
  t2  add an assertion at the point
       where the assumption is made
       |
       v
  t3  write a message that names the
       assumption and the function
       |
       v
  t4  run test suite
       -- if an assertion fires, a test is
          violating the assumption, which is
          a bug in the test or in the caller
       |
       v
  t5  commit. the assumption is asserted.
```

## 8. Implementation variants

**Runtime assertion.** The canonical variant. An assertion statement is
executed at runtime, and a violation raises an error. In Python, `assert`
raises `AssertionError`. In Java, `assert` raises `AssertionError`. In C
and C++, `assert` calls `abort`.

**Design by contract.** The assertion is a precondition, postcondition, or
invariant expressed in a contract. In Eiffel, contracts are language
constructs. In other languages, they are expressed through assertion
libraries or annotations.

**Static assertion.** In languages with compile time assertions, such as
C++ `static_assert` or Rust `const` assertions, the condition is checked
at compile time. This variant is used for conditions that can be evaluated
by the compiler, such as type properties or constant expressions.

**Type assertion.** In languages with dependent types or refinement
types, the assertion is a type annotation that the compiler checks. This
variant is used when the condition can be expressed as a type constraint,
for example that an integer is positive.

```python
# Python: before (assumption not checked)

def calculate_speed(distance: float, time: float) -> float:
    return distance / time  # assumes time != 0

# Python: after (assertion added)

def calculate_speed(distance: float, time: float) -> float:
    assert time != 0, "time must be non-zero, got " + str(time)
    return distance / time
```

```typescript
// TypeScript: before (assumption not checked)

function getItemBefore(items: string[], index: number): string {
    return items[index]; // assumes index is in range
}

// TypeScript: after (assertion added)

function getItem(items: string[], index: number): string {
    console.assert(index >= 0 && index < items.length,
        "index out of range");
    return items[index];
}
```

```java
public class SpeedCalculator {

    // Java: after (assertion with message)

    public double calculateSpeed(double distance, double time) {
        assert time != 0 : "time must be non-zero, got " + time;
        return distance / time;
    }
}

// Java: assertions must be enabled with -ea flag at runtime
```

## 9. Known production uses

**Python's `assert` statement** is the language level implementation of
runtime assertions. The Python documentation states that `assert`
expressions are tested for debugging purposes and that assertion failures
raise `AssertionError` ([Python assert documentation](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement),
verified 2026-08-13). The standard library itself uses assertions
extensively, for example in `statistics.mean` which asserts that the
input is not empty.

**Java's `assert` statement**, introduced in Java 1.4, is the language
level implementation. The Java documentation states that assertions are
disabled by default and must be enabled with the `-ea` flag
([Java Assertions documentation](https://docs.oracle.com/en/java/javase/21/language/assertions.html),
verified 2026-08-13). The JDK itself uses assertions internally for
preconditions and invariants in collection implementations.

## 10. Consequences

Positive.

- The assumption is stated explicitly, which documents it for the reader
  and catches violations at the point of the assumption.
- The assertion message helps a developer diagnose the root cause, because
  it names the assumption and the function.
- The assertion catches programming errors in development, which prevents
  them from reaching production as confusing errors.

Negative.

- If the assertion is disabled in production, the assumption is not
  checked at runtime, and a violation produces the same confusing error
  the assertion was supposed to prevent.
- The assertion adds a check on every execution, which has a cost that is
  usually negligible but may be measurable in hot loops.
- If the assertion is used for conditions that can legitimately occur at
  runtime, it crashes the program for a condition that error handling
  should recover from.
- The assertion message must be maintained, and a stale message that does
  not match the current assumption is worse than no message.

## 11. Failure modes and misuse

**Assertion for a runtime condition.** The assertion checks a condition
that can legitimately occur at runtime, for example a file not found, and
crashes the program for a condition that error handling should recover
from. The symptom is a crash in production for a condition that should have
been handled.

**Assertion that is disabled in production.** The assertion catches errors
only in development, and in production the same error produces a confusing
runtime failure. The symptom is a bug that is caught in development but
reaches production because the assertion was disabled.

**Assertion with a bad message.** The assertion fires with a message like
"assertion failed" that does not help the developer diagnose the root
cause. The symptom is an error that is caught at the right point but with
no diagnostic information.

**Over assertion.** Every line has an assertion, and the code is full of
checks that are not load bearing. The symptom is a function that is more
assertion than logic, which obscures the real code and slows execution.

## 12. Trade-off matrix

| Alternative | When checked | Error type | Production | When to prefer |
|---|---|---|---|---|
| Introduce Assertion | Development | Programming error | Disabled | Assumption is a precondition |
| Replace Exception with Test | Always | Runtime condition | Enabled | Condition can occur at runtime |
| Comment | Never | None | None | Assumption is documentation only |
| If check with throw | Always | Runtime error | Enabled | Condition must be checked in production |

## 13. Related and incompatible patterns

**Replace Exception with Test** (same catalog) is the alternative when
the condition can occur at runtime and must be handled, not asserted. An
if check that avoids the exception is better than an assertion that
crashes.

**Replace Assertion with Test** (same catalog) is the reverse, where an
assertion is replaced with an explicit test that handles the condition
gracefully rather than crashing.

**Encapsulate Variable** (same catalog) is related when the assumption is
that a field is in a valid state. The setter can assert the invariant,
which combines assertion with encapsulation.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by adding an assertion at the
point of the assumption. The steps are:

1. Identify the assumption the code depends on.
2. Determine the condition that must hold.
3. Add an assertion at the point where the assumption is made.
4. Write a message that names the assumption and the function.
5. Run the test suite. If an assertion fires, a test is violating the
   assumption, which is a bug in the test or in the caller.

**Path out.** The refactoring is reversed by Remove Assertion, which
removes the assertion when the assumption is no longer load bearing or
when the condition turns out to be a runtime condition that should be
handled, not asserted.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercises the function should pass unchanged, because the
assertion should not fire for valid inputs. If an assertion fires, a test
is providing an input that violates the assumption, which is either a bug
in the test or a signal that the assumption is too strict.

A new test should verify that the assertion fires for an invalid input.
Call the function with an input that violates the assumption and verify
that an `AssertionError` (or the language equivalent) is raised. This
test guards against a future change that removes or weakens the assertion.

## 16. Observability signals

The refactoring does not change behaviour for valid inputs, so the
observable signal in production is nothing. The one observable difference
is in error patterns: if an assertion fires in development, the error
appears at the assertion with a clear message, rather than at a downstream
operation with a confusing message. This is a positive observability
signal for development.

In production, where assertions are typically disabled, the observability
is unchanged, because the assertion does not execute. If the assertion
fires in production (because assertions are enabled or because the
language does not disable them), the crash is the signal that a
programming error has reached production.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the assertion can
catch a programming error that would produce a security vulnerability,
for example a null pointer that leads to a crash that can be exploited,
or an array index that leads to a buffer overflow. The assertion catches
the error at the point of the assumption, which is earlier than the
point where the vulnerability is exploited.

The privacy relevant case is that the assertion can catch a condition
that would leak data, for example an assertion that a list is empty
before it is returned to a caller who should not see its contents. The
assertion catches the leak at the point where the list should be empty,
which is earlier than the point where the data reaches the caller.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Introduce Assertion."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 10, "Introduce Assertion."
- Bertrand Meyer, *Object-Oriented Software Construction*, Prentice Hall,
  1988, "Design by Contract."
- C.A.R. Hoare, "Assertions: A Personal Perspective," 1973.
- Python Software Foundation, "The assert statement,"
  [https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement),
  verified 2026-08-13.
- Oracle, "Assertions,"
  [https://docs.oracle.com/en/java/javase/21/language/assertions.html](https://docs.oracle.com/en/java/javase/21/language/assertions.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
