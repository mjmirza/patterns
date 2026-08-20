---
name: Remove Dead Code
slug: remove-dead-code
family: 03-refactoring
category: Refactoring
aliases: [Delete Unreachable Code, Remove Unused Method, Eliminate Dead Code]
first_described: "Fowler 1999"
maturity: canonical
related: [inline-function, remove-subclass, collapse-hierarchy, extract-function, change-function-declaration]
incompatible_with: []
verified: 2026-08-13
---

# Remove Dead Code

## 1. Name, aliases, and lineage

The canonical name is **Remove Dead Code**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 6, "Composing Methods." The refactoring
survived into the second edition, Martin Fowler, *Refactoring. Improving
the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter
6, "A First Set of Refactorings," under the same name and with the same
mechanics.

The underlying idea, that code that is not called by anything should be
deleted, is one of the oldest ideas in software engineering. Brian
Kernighan and P.J. Plauger, in *Software Tools*, Addison-Wesley, 1976,
advise removing dead code because it is a maintenance burden that
produces no value. The Unix tradition of "do not keep what you do not
need" is the cultural root of the practice.

The term **dead code** is used by static analysis tools to refer to code
that is unreachable by any execution path. The alias **Remove Unused
Method** is the method specific variant. The alias **Delete Unreachable
Code** is used by linters and compilers that detect unreachable code.

## 2. Problem and context

A method or a block of code is not called by anything. It was once
called, but the caller was removed or changed, and the code was left
behind. It sits in the codebase, taking up space, confusing readers, and
creating a maintenance burden, because a change to the codebase must
account for it even though no one uses it.

The situation reads like this. A class has a method `calculateLegacyFee`
that was called from the billing module. The billing module was
rewritten to use a new fee calculation, and the call to
`calculateLegacyFee` was removed, but the method itself was left. The
method is now dead code: no test calls it, no production code calls it,
and a grep for its name returns only the definition. A reader who
encounters it must determine whether it is dead, which takes time, and a
change to the fee logic may accidentally update the dead method instead
of the live one.

The fix is to remove the dead code. Delete the method, and verify that
nothing breaks.

## 3. Forces

**Simplicity versus caution.** Dead code is a maintenance burden, and
removing it simplifies the codebase. But removing code that appears dead
but is actually called through reflection or string based dispatch
produces a runtime error. The force favours removal when the code is
verifiably dead, and favours caution when the call path is uncertain.

**Reversibility versus cleanliness.** Dead code can be recovered from
version control if it is needed later, which means removal is reversible.
The force favours removal because version control is the safety net.

**Documentation versus clutter.** Dead code that is left as
documentation of a previous approach is clutter, not documentation. The
commit message and the version history are the correct documentation, and
they are queryable and maintained. The force favours removal because the
code is not the right place for historical documentation.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A method or block is not called by any production code, test code, or
  framework configuration.
- A grep or a static analysis tool confirms the code is unreachable.
- The code was left behind after a caller was removed or changed.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The code is called via reflection, string based dispatch, or a
  framework that the static analysis tool cannot see. Removing it
  produces a runtime error that the tool did not detect.
- The code is part of a public API and consumers may call it. Removing
  it is a breaking change, not dead code removal.
- The code is a hook for future extension that has not been connected
  yet. Removing it means the extension must re create it.
- The language has dynamic dispatch that makes static analysis
  unreliable, and the code may be called through a mechanism that
  cannot be detected by grep.

## 5. Structure

The refactoring has one participant: the dead code that is removed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Service:                      class Service:
    process()                            process()
    calculateLegacyFee()              (calculateLegacyFee removed)

  (nobody calls calculateLegacyFee)   (dead code deleted)
```

## 7. Dynamics

```
  t0  identify code that appears dead
       |
       v
  t1  verify with grep and static analysis
       that no caller exists
       |
       v
  t2  check for reflection or dynamic dispatch
       that might call the code invisibly
       |
       v
  t3  delete the code
       |
       v
  t4  run test suite
       -- if green, the code was dead
       -- if red, the code was alive
       |
       v
  t5  commit. dead code removed.
```

## 8. Implementation variants

**Delete method.** The canonical variant. The method is deleted from
the class, and the test suite confirms nothing breaks.

**Delete block.** A block of statements inside a method is dead, and it
is removed from the method body.

**Delete file.** A whole file or module is dead, and it is deleted. This
variant requires checking imports and build configurations to confirm
nothing references the file.

```python
# Python: before (dead method)

class Service:
    def process(self, data: str) -> str:
        return data.upper()

    def calculate_legacy_fee(self, amount: float) -> float:
        # nobody calls this anymore
        return amount * 0.15

# Python: after (dead code removed)

class Service:
    def process(self, data: str) -> str:
        return data.upper()
```

```typescript
// TypeScript: before (dead method)

class ServiceBefore {
    process(data: string): string {
        return data.toUpperCase();
    }

    calculateLegacyFee(amount: number): number {
        // nobody calls this anymore
        return amount * 0.15;
    }
}

// TypeScript: after (removed)

class Service {
    process(data: string): string {
        return data.toUpperCase();
    }
}
```

```java
// Java: before (dead method)

class ServiceBefore {
    public String process(String data) {
        return data.toUpperCase();
    }

    // dead: no caller exists
    public double calculateLegacyFee(double amount) {
        return amount * 0.15;
    }
}

// Java: after (removed)

public class Service {
    public String process(String data) {
        return data.toUpperCase();
    }
}
```

## 9. Known production uses

**ESLint's `no-unreachable` rule** detects unreachable code in
JavaScript and TypeScript. The ESLint documentation states that the rule
disallows unreachable code after `return`, `throw`, `continue`, and
`break` statements, because a statement placed after one of these
control-flow exits cannot be executed on any path
([ESLint no-unreachable](https://eslint.org/docs/latest/rules/no-unreachable),
verified 2026-08-19).

**The Rust compiler's dead code analysis** is a language level
implementation. The Rust compiler reports `dead_code` warnings for
functions that are never called, and the documentation states that the
lint detects functions that are not reachable from any public entry
point ([Rust dead_code lint](https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html#dead-code),
verified 2026-08-13).

## 10. Consequences

Positive.

- The codebase is smaller, which reduces the maintenance burden and the
  time to understand it.
- A reader no longer needs to determine whether the dead code is live,
  which saves time.
- A change to the codebase no longer needs to account for the dead code,
  which reduces the risk of accidentally updating it.

Negative.

- If the code was alive through a call path that was not detected,
  removing it produces a runtime error.
- The code is lost from the working tree, and recovering it requires
  version control archaeology.

## 11. Failure modes and misuse

**Removing code called by reflection.** The code appears dead because
grep does not find a caller, but it is called through `getattr` in Python
or `Method.invoke` in Java. The symptom is a runtime error that appears
only when the reflective call path executes.

**Removing a public API method.** The method is not called internally,
but it is part of a public API and consumers call it. Removing it is a
breaking change, not dead code removal.

**Removing a hook for future extension.** The method is not called yet,
but it is a hook that a future feature will connect. Removing it means the
feature must re create it.

## 12. Trade-off matrix

| Alternative | Code count | Reversibility | When to prefer |
|---|---|---|---|
| Remove Dead Code | -1 | Via version control | Code is verifiably dead |
| Keep dead code | 0 | None | Code may be alive through reflection |
| Inline Function | -1 (caller gets body) | Via version control | Function is trivial, one caller |
| Extract Function | +1 | Via version control | Block deserves a name |

## 13. Related and incompatible patterns

**Inline Function** (same catalog) is related: a function with one
caller can be inlined, which removes the function. If the function is
dead, Remove Dead Code is simpler than Inline Function.

**Remove Subclass** (same catalog) is the class level version: a
subclass that is never instantiated is dead and should be removed.

**Collapse Hierarchy** (same catalog) is related: an empty hierarchy
level is dead structure and should be collapsed.

## 14. Refactoring path in and out

**Path in.** Verify the code is dead, delete it, run tests.

**Path out.** Recover the code from version control if it turns out to
be alive.

## 15. Testing and verification

The test suite is the primary verification. After the removal, every
test should pass, because the dead code was not called by anything. If a
test fails, the code was alive, and it should be restored.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The code is smaller, which may reduce the
binary size or the module load time, but the runtime behaviour is
identical.

## 17. Security and privacy implications

The refactoring improves security when the dead code contained a security
vulnerability that was not being exploited because the code was dead.
Removing it eliminates the vulnerability. This is a positive security
signal.

The privacy relevant case is when the dead code processed sensitive data,
and removing it eliminates the data processing. This is a positive privacy
signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Remove Dead Code."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Remove Dead Code."
- Brian Kernighan and P.J. Plauger, *Software Tools*, Addison-Wesley,
  1976.
- ESLint, "no-unreachable,"
  [https://eslint.org/docs/latest/rules/no-unreachable](https://eslint.org/docs/latest/rules/no-unreachable),
  verified 2026-08-19.
- Rust, "dead_code lint,"
  [https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html#dead-code](https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html#dead-code),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
