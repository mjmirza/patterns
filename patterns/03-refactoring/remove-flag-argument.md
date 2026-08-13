---
name: Remove Flag Argument
slug: remove-flag-argument
family: 03-refactoring
category: Refactoring
aliases: [Remove Boolean Parameter, Split Flag Function, Replace Boolean with Methods]
first_described: "Fowler 2018"
maturity: canonical
related: [parameterize-function, change-function-declaration, extract-function, replace-conditional-with-polymorphism, decompose-conditional]
incompatible_with: []
verified: 2026-08-13
---

# Remove Flag Argument

## 1. Name, aliases, and lineage

The canonical name is **Remove Flag Argument**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 11, "Making Calls Simpler." The
refactoring is new to the second edition, reflecting the growing
consensus in the software engineering community that boolean flag
parameters are a code smell. In the first edition (1999), the broader
Parameterize Method covered the case, but Fowler split it out because
the mechanics differ: the flag is not a value that parameterizes a
general function, it is a selector between two unrelated behaviours.

The underlying idea, that a function should do one thing, not select
between two things based on a boolean, is one of the oldest principles
of clean code. Robert C. Martin, in *Clean Code*, Prentice Hall, 2008,
chapter 3, writes that flag arguments "complicate the signature of the
function loudly proclaiming that this function does more than one thing."
Fowler's refactoring is the mechanical path from a flag to two functions.

The term **flag argument** comes from Martin Fowler's writing, where a
flag is a boolean parameter that selects between behaviours. The alias
**Remove Boolean Parameter** is used in the static analysis community.
The alias **Replace Boolean with Methods** is used in the Java community.

## 2. Problem and context

A function takes a boolean parameter that selects between two different
behaviours. The caller must pass `true` or `false` and must know which
value selects which behaviour. The function body has a conditional that
branches on the flag, and the two branches do unrelated things. The
function name does not communicate which behaviour is selected, because
the same name is used for both.

The situation reads like this. A function `sendNotification(recipient,
isUrgent)` sends either an urgent or a normal notification. The caller
must pass `true` for urgent and `false` for normal, and the function
body has `if isUrgent: sendUrgent() else: sendNormal()`. A reader who
sees `sendNotification(user, true)` must know that `true` means urgent,
which is not obvious from the call site. The function does two things,
and the flag is the selector.

The fix is to remove the flag argument. Replace `sendNotification` with
two functions: `sendUrgentNotification(recipient)` and
`sendNormalNotification(recipient)`. Each function does one thing, and
the name communicates which.

## 3. Forces

**Readability versus parameter count.** A flag parameter is one
parameter, which is fewer than two functions. But the flag is not
readable at the call site, because `true` does not communicate "urgent."
Two functions have clear names, which is readable. The force favours two
functions when the readability benefit exceeds the function count cost.

**Single responsibility versus convenience.** A function with a flag
does two things, which violates the single responsibility principle. Two
functions each do one thing. The force favours two functions when the
responsibilities are genuinely different.

**Call site clarity versus brevity.** A call site with a flag is brief
but unclear: `sendNotification(user, true)`. A call site with a named
function is clear but longer: `sendUrgentNotification(user)`. The force
favours clarity over brevity when the flag is not obvious.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A function takes a boolean parameter that selects between two
  behaviours, and the flag is not obvious at the call site.
- The two behaviours are unrelated, not variants of the same operation.
- The function name does not communicate which behaviour is selected.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The parameter is not a boolean flag but a genuine value that
  parameterizes a general function. For example `setMaxAge(seconds)` is
  parameterized, not flagged.
- The two behaviours are variants of the same operation, and the flag is
  a natural parameter. For example `sort(ascending=True)` is a flag, but
  the ascending and descending sorts are the same operation in different
  directions, and splitting them into two functions is over splitting.
- The function is part of a public API and removing the flag breaks
  consumers.

## 5. Structure

The refactoring has one participant: the flag argument that is replaced
by two functions.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  notify(recipient, isUrgent)         notifyUrgent(recipient)
    if isUrgent:                        sendUrgent(recipient)
      sendUrgent()
    else:                            notifyNormal(recipient)
      sendNormal()                      sendNormal(recipient)

  caller:                             caller:
    notify(user, true)                  notifyUrgent(user)
    notify(user, false)                notifyNormal(user)
```

## 7. Dynamics

```
  t0  identify function with boolean flag
       |
       v
  t1  create two functions, one per behaviour
       |
       v
  t2  move each branch's body into its function
       |
       v
  t3  update callers to call the right function
       |
       v
  t4  remove the old flagged function
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the flag is removed.
```

## 8. Implementation variants

**Two named functions.** The canonical variant. The flagged function is
replaced by two named functions, one per behaviour.

**Enum parameter.** The flag is replaced by an enum with named values,
which communicates the behaviour at the call site without splitting the
function. This variant is used when the function has too many behaviours
to split into separate functions.

**Named arguments.** In languages with named arguments, the flag is
given a name at the call site: `notify(recipient, urgent=true)`. This
variant is a compromise that keeps the single function but makes the
flag readable.

```python
# Python: before (flag argument)

def send_notification(recipient: str, is_urgent: bool) -> None:
    if is_urgent:
        print(f"URGENT: notifying {recipient}")
    else:
        print(f"notifying {recipient}")

# caller: send_notification("alice", True)  # unclear

# Python: after (two functions)

def send_urgent_notification(recipient: str) -> None:
    print(f"URGENT: notifying {recipient}")

def send_normal_notification(recipient: str) -> None:
    print(f"notifying {recipient}")

# caller: send_urgent_notification("alice")  # clear
```

```typescript
// TypeScript: before (flag argument)

function sendNotification(recipient: string, isUrgent: boolean): void {
    if (isUrgent) {
        console.log(`URGENT: notifying ${recipient}`);
    } else {
        console.log(`notifying ${recipient}`);
    }
}

// caller: sendNotification("alice", true);  // unclear

// TypeScript: after (two functions)

function sendUrgentNotification(recipient: string): void {
    console.log(`URGENT: notifying ${recipient}`);
}

function sendNormalNotification(recipient: string): void {
    console.log(`notifying ${recipient}`);
}

// caller: sendUrgentNotification("alice");  // clear
```

```java
// Java: after (two methods)

public void sendUrgentNotification(String recipient) {
    System.out.println("URGENT: notifying " + recipient);
}

public void sendNormalNotification(String recipient) {
    System.out.println("notifying " + recipient);
}
// caller: sendUrgentNotification("alice");
```

## 9. Known production uses

**SonarQube's rule S1788, "Boolean methods should not be named with
negating prefixes"** detects the pattern this refactoring targets and
suggests splitting. SonarSource documents that boolean parameters
complicate method calls and that named methods are clearer
([SonarSource rule S1788](https://rules.sonarsource.com/java/rspec-S1788/),
verified 2026-08-13).

**JetBrains' inspection "Boolean parameter is passed as literal"**
detects call sites where a boolean literal is passed and suggests
extracting a named function or using a named argument
([JetBrains Inspections](https://www.jetbrains.com/help/idea/code-inspection.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- Each function does one thing, which is the single responsibility
  principle.
- The call site is clear: the function name communicates the behaviour.
- The function body has no conditional, which is simpler.

Negative.

- The function count increases, which adds names to the codebase.
- If the two behaviours share setup or cleanup, the shared code is
  duplicated in both functions, unless extracted into a helper.

## 11. Failure modes and misuse

**Splitting a parameterized function.** The parameter is not a flag but
a value, and splitting the function into two loses the generality. For
example, splitting `setMaxAge(seconds)` into `setMaxAgeTo60()` and
`setMaxAgeTo120()` is absurd.

**Over splitting.** Every boolean parameter is split, producing a
proliferation of functions that is harder to navigate than the original
flagged function.

## 12. Trade-off matrix

| Alternative | Function count | Call site clarity | When to prefer |
|---|---|---|---|
| Remove Flag Argument | +1 | High | Flag selects unrelated behaviours |
| Parameterize Function | 0 | Low | Flag is a genuine parameter |
| Named Arguments | 0 | Medium | Language supports named args |
| Enum Parameter | 0 | High | Multiple behaviours, not just two |

## 13. Related and incompatible patterns

**Parameterize Function** (same catalog) is the alternative when the
parameter is a genuine value, not a flag.

**Change Function Declaration** (same catalog) is the mechanism for
renaming the functions and updating callers.

**Decompose Conditional** (same catalog) is related when the
conditional on the flag is complex and the branches need names.

## 14. Refactoring path in and out

**Path in.** Create two functions, move each branch's body, update
callers, remove the old function.

**Path out.** Re introduce the flag by creating a function that takes a
boolean and delegates to the two functions, which is rarely applied.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called the flagged function should call the corresponding
named function and should produce the same result.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The function names in traces change, which is a
minor format change that is actually an improvement because the trace
now shows which behaviour was executed.

## 17. Security and privacy implications

The refactoring does not change what data is processed, so it does not
change the security surface.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Remove Flag Argument."
- Robert C. Martin, *Clean Code*, Prentice Hall, 2008, chapter 3.
- SonarSource, "Boolean method names," rule S1788,
  [https://rules.sonarsource.com/java/rspec-S1788/](https://rules.sonarsource.com/java/rspec-S1788/),
  verified 2026-08-13.
- JetBrains, "Code Inspection,"
  [https://www.jetbrains.com/help/idea/code-inspection.html](https://www.jetbrains.com/help/idea/code-inspection.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
