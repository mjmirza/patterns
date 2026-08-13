---
name: Move Statements to Callers
slug: move-statements-to-callers
family: 03-refactoring
category: Refactoring
aliases: [Extract Statements to Caller, Push Statements Out]
first_described: "Fowler 2018"
maturity: canonical
related: [move-statements-into-function, extract-function, inline-function, move-function, replace-function-with-command]
incompatible_with: []
verified: 2026-08-13
---

# Move Statements to Callers

## 1. Name, aliases, and lineage

The canonical name is **Move Statements to Callers**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
The refactoring is new to the second edition and is the inverse of Move
Statements into Function. The two form a pair: one moves statements into
the function, the other moves them out.

The situation arises when a function performs statements that should be
the caller's responsibility, not the function's. The function was given
too much to do, or the statements were placed inside the function for
convenience but do not belong there. The function now has a second
responsibility, and callers that do not need the extra statements are
forced to accept them.

## 2. Problem and context

A function performs statements that vary by caller or that are not the
function's responsibility. The statements were placed inside the function
because every caller at the time needed them, but now some callers need
the statements and some do not, or the statements need to vary by call
site. The function is doing too much, and the extra statements are
coupling it to concerns that should be the caller's.

The situation reads like this. A function `processOrder` opens a
transaction, processes the order, commits the transaction, and logs the
result. Every caller that needs a transaction calls `processOrder` and
gets the transaction management for free. But now a caller needs to
process multiple orders in a single transaction, and `processOrder`
commits after each order, which prevents the batch. The transaction
management is inside the function, but it should be the caller's
responsibility, because the caller knows the transaction boundary.

The fix is to move the transaction statements to the callers. Remove the
open and commit from `processOrder`, and every caller that needs a
transaction opens and commits it. The function now processes the order
and returns the result, and the caller manages the transaction.

## 3. Forces

**Responsibility versus convenience.** The function provides convenience
by performing the statements for the caller, which is nice when every
caller needs them. But when callers need to vary the statements, the
convenience becomes a constraint. The force favours moving when the
statements need to vary.

**Coupling versus simplicity.** The function is coupled to the resource
the statements manage, for example a transaction or a connection. Moving
the statements to the caller decouples the function, but the caller
must now manage the resource. The force favours moving when the coupling
is wrong.

**Single responsibility versus convenience.** The function has a second
responsibility when it manages the resource in addition to its primary
task. Moving the statements to the caller gives the function one
responsibility. The force favours moving when the second responsibility is
not the function's.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function performs statements that are not its responsibility, and
  the statements should be the caller's.
- Some callers need the statements and some do not, and the function
  forces all callers to accept them.
- The statements need to vary by call site, and the function cannot
  parameterise them without a complex interface.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- Every caller needs the statements, and they are always the same. The
  function is the right owner, and moving them would duplicate them.
- The statements manage a resource that the function is the right owner
  of, for example a connection that the function opens and closes as
  part of its contract.

## 5. Structure

The refactoring has one participant: the statements inside the function
that are moved to every caller.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  function processOrder(order):       function processOrder(order):
    tx = open()                          result = compute(order)
    result = compute(order)              return result
    commit(tx)
    log(result)                      caller:
    return result                      tx = open()
                                       result = processOrder(order)
  caller:                              commit(tx)
    result = processOrder(order)       log(result)
                                      (statements moved to caller)
  (function manages transaction)
```

## 7. Dynamics

```
  t0  identify statements in the function
       that should be the caller's
       |
       v
  t1  copy the statements to every caller
       |
       v
  t2  remove the statements from the function
       |
       v
  t3  run test suite
       |
       v
  t4  commit. the statements are moved.
```

## 8. Implementation variants

**Move before.** Statements at the start of the function are moved to
before the call in every caller.

**Move after.** Statements at the end of the function are moved to after
the call in every caller.

**Move both.** Statements at the start and end are moved to surround the
call, forming a wrapper in the caller.

```python
# Python: before (function manages transaction)

def process_order(order):
    tx = begin_transaction()
    result = compute(order)
    commit(tx)
    log(result)
    return result

# Python: after (transaction moved to caller)

def process_order(order):
    return compute(order)

# caller:
tx = begin_transaction()
result = process_order(order)
commit(tx)
log(result)
```

```typescript
// TypeScript: after (caller manages transaction)

function processOrder(order: Order): Result {
    return compute(order);
}

// caller:
const tx = beginTransaction();
const result = processOrder(order);
commit(tx);
log(result);
```

```java
// Java: after (caller manages transaction)

public Result processOrder(Order order) {
    return compute(order);
}

// caller:
Transaction tx = beginTransaction();
Result result = processOrder(order);
tx.commit();
log(result);
```

## 9. Known production uses

**Spring's `@Transactional` annotation** is the framework level
mechanism for the inverse of this refactoring. When the transaction
management is moved into the function, Spring's annotation does it
declaratively. When the transaction needs to be in the caller, the
annotation is removed and the caller manages the transaction
([Spring Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html),
verified 2026-08-13).

**Python's explicit transaction management** in the `sqlite3` module is
the language level example of statements in the caller. The caller opens
the transaction, executes statements, and commits, rather than the
function managing the transaction internally
([sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The function has one responsibility, which is its primary task.
- The caller controls the resource lifecycle, which allows batching and
  varying the transaction boundary.
- The function is decoupled from the resource, which makes it testable
  without the resource.

Negative.

- Every caller must perform the statements, which is duplication when
  they are the same.
- A caller that forgets the statements produces a bug, for example a
  missing commit.
- The function's contract is now weaker, because it does not guarantee
  the resource management.

## 11. Failure modes and misuse

**Moving statements that every caller needs.** The statements are the
same at every call site, and moving them duplicates them, which is the
opposite of what Move Statements into Function does.

**Moving statements that the function should own.** The statements are
part of the function's contract, and moving them breaks the contract.

## 12. Trade-off matrix

| Alternative | Ownership | Duplication | When to prefer |
|---|---|---|---|
| Move Statements to Callers | Caller | Present | Statements vary by caller |
| Move Statements into Function | Function | Eliminated | Same statements at every call |
| Extract Function | New function | Eliminated | Statements are a reusable block |
| Replace Function with Command | Command object | Eliminated | Function needs undo/queue |

## 13. Related and incompatible patterns

**Move Statements into Function** (same catalog) is the inverse. It
moves statements from the callers into the function.

**Extract Function** (same catalog) can be applied after the move to
extract the moved statements into a helper function, which avoids
duplication when the statements are the same.

## 14. Refactoring path in and out

**Path in.** Copy the statements from the function to every caller,
then remove them from the function.

**Path out.** Move the statements back into the function (Move Statements
into Function) when the statements turn out to be the same at every call
site.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test should produce the same result, now with the statements at the call
site.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The transaction or resource management may appear
differently in traces, because it is now at the call site.

## 17. Security and privacy implications

The refactoring may affect security when the statements manage a security
relevant resource. Moving them to the caller means the caller is now
responsible for the security, and a caller that forgets the close
produces a security vulnerability. This is a security risk that should be
documented.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Move Statements to Callers."
- Spring, "Transaction Management,"
  [https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html),
  verified 2026-08-13.
- Python Software Foundation, "sqlite3,"
  [https://docs.python.org/3/library/sqlite3.html](https://docs.python.org/3/library/sqlite3.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
