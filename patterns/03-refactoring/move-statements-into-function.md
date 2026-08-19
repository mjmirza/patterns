---
name: Move Statements into Function
slug: move-statements-into-function
family: 03-refactoring
category: Refactoring
aliases: [Move Statements to Called Function, Absorb Statements]
first_described: "Fowler 2018"
maturity: canonical
related: [move-statements-to-callers, extract-function, inline-function, move-function, combine-functions-into-transform]
incompatible_with: []
verified: 2026-08-13
---

# Move Statements into Function

## 1. Name, aliases, and lineage

The canonical name is **Move Statements into Function**, introduced by
Martin Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
The refactoring is new to the second edition. It does not appear in the
first edition (1999), because the first edition's Extract Method covered
the broader case and the specific case of moving statements that were
forgotten in an extraction was not separately catalogued.

The underlying situation arises after Extract Function has been applied
imperfectly: some statements that should have been part of the extracted
function's body were left in the caller, and the caller now performs a
sequence of statements that are duplicated before or after every call to
the extracted function. The refactoring moves those statements into the
function, so the function owns the full sequence and the caller calls it
without the surrounding boilerplate.

## 2. Problem and context

You have a function that is called from multiple places, and every caller
performs the same statements immediately before or after the call. The
statements are duplicated, and a change to the sequence requires finding
and updating every caller. The statements should be inside the function,
but they were left outside because the function was extracted without
including them, or because the statements were added later and the author
did not realise they belonged inside the function.

The situation reads like this. A function `emit` sends a line of output.
Every caller opens the connection, calls `emit`, and closes the
connection. The open and close are duplicated at every call site, and a
caller that forgets to close produces a connection leak. The open and
close should be inside `emit`, so the function manages the connection
lifecycle and the caller just calls it.

The fix is to move the statements into the function. Copy the open and
close into `emit`, remove them from every caller, and the function now
owns the full sequence.

## 3. Forces

**Duplication versus ownership.** Duplicated statements at every call site
are a maintenance burden. Moving them into the function gives the function
ownership of the full sequence, which eliminates the duplication. The force
favours moving when the statements are the same at every call site.

**Coupling versus convenience.** Moving statements into the function
couples the function to the resources the statements manage, for example
a connection or a transaction. The function now opens and closes the
connection, which is convenient but couples the function to the connection
lifecycle. The force favours moving when the function is the right owner
of the resource.

**Single responsibility versus convenience.** Moving statements into the
function may give it a second responsibility, for example managing a
connection in addition to emitting output. The force favours keeping the
statements in the caller when the function's responsibility is narrow and
the statements are a different responsibility.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The same statements appear before or after every call to the function,
  and the statements are duplicated.
- A caller that forgets the statements produces a bug, for example a
  connection leak or a missing cleanup.
- The statements are always the same, not varying by call site.
- The function is the right owner of the statements' responsibility.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The statements vary by call site, and moving them into the function
  would require parameters to select the variant, which is more complex
  than the duplication.
- The function's responsibility does not include the statements, and
  moving them would violate the Single Responsibility Principle.
- The statements manage a resource that the function should not own, for
  example a database transaction that the caller manages as part of a
  larger unit of work.

## 5. Structure

The refactoring has one participant.

- **The statements.** A sequence of statements that appear at every call
  site. After the refactoring, they are inside the function and removed
  from every caller.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  function emit(line):               function emit(line):
    send(line)                         open()
                                       send(line)
  caller:                               close()
    open()
    emit("hello")                    caller:
    close()                             emit("hello")
    open()
    emit("world")                    (open/close moved into emit)
    close()

  (open/close duplicated at every    (function owns full sequence)
   call site)
```

## 7. Dynamics

```
  t0  identify statements duplicated
       before or after every call
       |
       v
  t1  copy the statements into the function
       |
       v
  t2  remove the statements from every caller
       |
       v
  t3  run test suite
       |
       v
  t4  commit. the statements are moved.
```

## 8. Implementation variants

**Move before.** Statements that appear before every call are moved to
the start of the function. This is the open variant, for example opening
a connection.

**Move after.** Statements that appear after every call are moved to the
end of the function. This is the close variant, for example closing a
connection.

**Move both.** Statements before and after every call are moved to the
start and end of the function, forming a wrapper. This is the open and
close variant, which is the most common.

```python
# Python: before (open/close duplicated)

def emit(line: str) -> None:
    conn.send(line)

# caller:
conn.open()
emit("hello")
conn.close()
conn.open()
emit("world")
conn.close()

# Python: after (moved into function)

def emit(line: str) -> None:
    conn.open()
    conn.send(line)
    conn.close()

# caller:
emit("hello")
emit("world")
```

```typescript
declare const conn: {
    open(): void;
    send(line: string): void;
    close(): void;
};

// TypeScript: after (moved into function)

function emit(line: string): void {
    conn.open();
    conn.send(line);
    conn.close();
}

// caller:
emit("hello");
emit("world");
```

```java
class Connection implements AutoCloseable {
    void send(String line) {}

    @Override
    public void close() {}
}

public class EmitService {

    private Connection openConnection() {
        return new Connection();
    }

    // Java: after (moved into function, try-with-resources)

    public void emit(String line) {
        try (Connection conn = openConnection()) {
            conn.send(line);
        }  // close is automatic
    }

    // caller:
    public void run() {
        emit("hello");
        emit("world");
    }
}
```

## 9. Known production uses

**Python's context managers** (`with` statement) are the language level
mechanism for this refactoring. A context manager's `__enter__` and
`__exit__` methods are the open and close statements that are moved into
the resource's usage, and every `with` block calls them automatically.
The Python documentation states that the `with` statement wraps the
execution of a block with methods defined by a context manager
([Python with statement](https://docs.python.org/3/reference/compound_stmts.html#with),
verified 2026-08-13).

**Java's try-with-resources**, introduced in Java 7, is the equivalent
mechanism. The `try` block automatically closes any `AutoCloseable`
resource, which moves the close statement into the language construct
rather than the caller
([Java try-with-resources](https://docs.oracle.com/en/java/javase/21/language/try-with-resources.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The duplicated statements are eliminated, which reduces the maintenance
  burden and the risk of forgetting the close.
- The function owns the full sequence, which means a change to the
  sequence is made in one place.
- The caller is simpler: one call instead of open, call, close.

Negative.

- The function now manages the resource, which is a second responsibility
  if the resource is not the function's primary concern.
- The function is coupled to the resource lifecycle, which means it
  cannot be called without the resource management.
- If the caller needs the resource to remain open across multiple calls,
  the refactoring does not apply, because the function closes after
  every call.

## 11. Failure modes and misuse

**Moving statements that vary by caller.** The statements are not the
same at every call site, and moving them into the function requires
parameters or conditionals that are more complex than the duplication.

**Moving statements that manage a long lived resource.** The resource
should remain open across multiple calls, and moving the close into the
function closes it after every call, which is wrong. The symptom is a
connection that is opened and closed on every call, which is a
performance regression.

## 12. Trade-off matrix

| Alternative | Duplication | Ownership | When to prefer |
|---|---|---|---|
| Move Statements into Function | Eliminated | Function owns sequence | Same statements at every call |
| Move Statements to Callers | Eliminated | Caller owns sequence | Statements vary by caller |
| Extract Function | Eliminated | New function owns sequence | Statements are a reusable block |
| Keep duplicated | Present | None | Statements are trivial, vary by site |

## 13. Related and incompatible patterns

**Move Statements to Callers** (same catalog) is the inverse. It moves
statements from the function to the callers, when the statements should
not be inside the function.

**Extract Function** (same catalog) is the broader refactoring that
created the function in the first place. Move Statements into Function
fixes an imperfect extraction.

**Inline Function** (same catalog) is the opposite direction: it moves
the function's body into the caller.

## 14. Refactoring path in and out

**Path in.** Copy the duplicated statements into the function and remove
them from every caller.

**Path out.** Move the statements back to the callers (Move Statements to
Callers) when the function should not own them.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test should produce the same result, now through the function that owns
the full sequence.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The resource lifecycle may appear differently in
traces, because the open and close are now inside the function rather
than at the call site.

## 17. Security and privacy implications

The refactoring improves security when the statements manage a security
relevant resource, for example closing a connection that could be
exploited if left open. The function now owns the close, which prevents
the connection leak that a caller would produce by forgetting the close.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Move Statements into
  Function."
- Python Software Foundation, "The with statement,"
  [https://docs.python.org/3/reference/compound_stmts.html#with](https://docs.python.org/3/reference/compound_stmts.html#with),
  verified 2026-08-13.
- Oracle, "try-with-resources,"
  [https://docs.oracle.com/en/java/javase/21/language/try-with-resources.html](https://docs.oracle.com/en/java/javase/21/language/try-with-resources.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
