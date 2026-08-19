---
name: Introduce Special Case
slug: introduce-special-case
family: 03-refactoring
category: Refactoring
aliases: [Introduce Null Object, Null Object Pattern, Special Case Pattern]
first_described: "Fowler 1999"
maturity: canonical
related: [change-reference-to-value, change-value-to-reference, extract-class, replace-conditional-with-polymorphism, extract-function]
incompatible_with: []
verified: 2026-08-13
---

# Introduce Special Case

## 1. Name, aliases, and lineage

The canonical name is **Introduce Special Case**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 9, "Moving Features." In the first
edition (1999), the same operation appeared as **Introduce Null Object**,
which was the name used for the Null Object pattern from the patterns
community. Fowler renamed it to Introduce Special Case in the second
edition because the technique applies to any special case, not only null,
for example an unknown customer, a missing site, or a default site.

The underlying pattern, the **Null Object pattern**, was described by
Bruce Anderson in "Null Object" (1996) and popularised by Bobby Woolf in
*The Pattern Almanac 1998* (Addison-Wesley, 1998). The pattern states
that instead of returning null and forcing every caller to check, return
an object that implements the same interface but produces the do nothing
or default behaviour. Martin Fowler's refactoring is the mechanical path
from null checks to a Null Object, and the second edition generalises it
to any special case.

The term **Special Case** comes from Martin Fowler, *Analysis Patterns*,
Addison-Wesley, 1997, where a Special Case is a variation of an object
that represents a specific, named case that requires different behaviour
from the general case. The Null Object is the most common special case,
but the pattern is broader: an Unknown Customer, a Guest User, or a
Default Site are all special cases.

## 2. Problem and context

You have code that checks for null, or for a special value that means
"no value" or "unknown," before every operation on the object. The check
is duplicated at every call site, and a caller that forgets the check
produces a null pointer error or an undefined behaviour. The check is
boilerplate that obscures the real logic, and it is a recurring source of
bugs when a new code path forgets to check.

The situation reads like this. A `Customer` object may be null when the
customer is not found. Every function that uses a customer starts with
`if customer is null: return` or `if customer is null: throw`. The check
is in every function, and a new function that forgets the check produces
a null pointer error in production. The team has a convention that every
customer reference must be null checked, but conventions are not
enforced, and the check is boilerplate that adds three lines to every
function.

The fix is to introduce a special case. Create an `UnknownCustomer`
class that implements the same interface as `Customer` but produces the
do nothing behaviour for every method. Instead of returning null, return
an `UnknownCustomer` instance. Callers no longer check for null, because
the object they receive is never null. The `UnknownCustomer` handles
every call gracefully, and the boilerplate is eliminated.

## 3. Forces

**Safety versus simplicity.** A null check at every call site is safe
when it is done correctly, but it is simple to forget. A special case
object is safe by construction, because the object handles every call.
The force favours the special case when the safety benefit of never
having a null exceeds the complexity cost of a new class.

**Boilerplate versus indirection.** A null check is boilerplate that
obscures the real logic. A special case object is indirection that
removes the boilerplate but adds a class. The force favours the special
case when the boilerplate is significant and the indirection is minimal.

**Explicitness versus transparency.** A null check is explicit: the
caller knows it is checking for null. A special case object is
transparent: the caller does not know it is dealing with a special case.
The force favours the special case when the caller's logic does not need
to distinguish between the general case and the special case.

**Flexibility versus rigidity.** A special case object has fixed
behaviour, which is rigid if the behaviour needs to vary by call site.
A null check gives the caller the flexibility to handle each case
differently. The force favours the special case when the behaviour is
the same at every call site, and favours the null check when the caller
needs to vary the handling.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The code checks for null or for a special value at many call sites,
  and the check is always the same, for example returning a default or
  doing nothing.
- A caller that forgets the check produces a crash, and the crash is a
  recurring source of production incidents.
- The special case's behaviour is the same at every call site, which means
  the caller does not need to vary the handling.
- The object has an interface that the special case can implement, which
  means the special case can provide the same methods with do nothing or
  default behaviour.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The null or special value means different things at different call
  sites, and the caller needs to handle each case differently. The
  special case would force every call site into the same behaviour,
  which is wrong.
- The null check is in one or two places, and the boilerplate is
  minimal. The special case adds a class and indirection that exceed the
  benefit.
- The object does not have an interface that the special case can
  implement, for example the object is a primitive value. A null integer
  cannot be replaced by a special case integer without wrapping it.
- The language has optional types, such as Rust's `Option` or Kotlin's
  `?`, which make null checks explicit at the type level. The type system
  enforces the check, and the special case is not needed.

## 5. Structure

The refactoring has one participant.

- **The special case.** A class that implements the same interface as the
  general case but produces the do nothing or default behaviour. After
  the refactoring, the function returns the special case instead of null,
  and callers no longer check for null.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  customer = find(id)                 customer = find(id)
  if customer is null:                  // customer is never null
      return                          // UnknownCustomer handles everything
  customer.charge(amount)             customer.charge(amount)
                                       // UnknownCustomer.charge is a no-op

  (null check at every call site)     (no null check, special case handles)
```

## 7. Dynamics

```
  t0  identify repeated null checks
       for the same type
       |
       v
  t1  create a special case class that
       implements the same interface
       |
       v
  t2  implement do-nothing or default
       behaviour for each method
       |
       v
  t3  change the function that returned
       null to return the special case
       |
       v
  t4  remove the null checks from
       every call site
       |
       v
  t5  run test suite
       -- every call site should work
          without the null check
       |
       v
  t6  commit. the special case is introduced.
```

## 8. Implementation variants

**Singleton special case.** The canonical variant. The special case is a
singleton, because there is only one unknown customer or one null site,
and every reference to the special case is the same instance. This is the
variant Fowler describes in both editions.

**Immutable value special case.** The special case is an immutable value
object, which is safe to share because it cannot be mutated. This variant
combines Introduce Special Case with the value object contract.

**Polymorphic special case.** The special case is a subclass of the
general case that overrides methods with do nothing behaviour. This
variant uses inheritance to provide the special case behaviour, and it
is the variant used when the general case is already a class hierarchy.

**Functional default.** In functional languages, the special case is a
default value or a function that returns the default, which is the
functional variant of the null object.

```python
# Python: before (null checks everywhere)

class Customer:
    def __init__(self, name: str):
        self.name = name

    def charge(self, amount: float) -> None:
        print(f"Charging {self.name} {amount}")

def find_customer(id: int) -> Customer | None:
    if id in database:
        return Customer(database[id])
    return None

# caller:
customer = find_customer(id)
if customer is not None:
    customer.charge(50.0)

# Python: after (special case)

class Customer:
    def __init__(self, name: str):
        self.name = name

    def charge(self, amount: float) -> None:
        print(f"Charging {self.name} {amount}")

class UnknownCustomer(Customer):
    """Special case: no name, charge is a no-op."""

    def __init__(self):
        super().__init__("unknown")

    def charge(self, amount: float) -> None:
        pass  # do nothing

def find_customer(id: int) -> Customer:
    if id in database:
        return Customer(database[id])
    return UnknownCustomer()

# caller: no null check needed
customer = find_customer(id)
customer.charge(50.0)  # safe, even for unknown
```

```typescript
declare const database: Record<number, string>;

// TypeScript: after (special case implements interface)

interface Customer {
    name: string;
    charge(amount: number): void;
}

class RealCustomer implements Customer {
    constructor(public name: string) {}

    charge(amount: number): void {
        console.log(`Charging ${this.name} ${amount}`);
    }
}

class UnknownCustomer implements Customer {
    readonly name = "unknown";

    charge(_amount: number): void {
        // do nothing
    }
}

function findCustomer(id: number): Customer {
    return id in database
        ? new RealCustomer(database[id])
        : new UnknownCustomer();
}
```

```java
// Java: after (special case as subclass)

public class Customer {
    private final String name;

    public Customer(String name) { this.name = name; }

    public String getName() { return name; }

    public void charge(double amount) {
        System.out.println("Charging " + name + " " + amount);
    }
}

class UnknownCustomer extends Customer {
    private static final UnknownCustomer INSTANCE = new UnknownCustomer();

    public static UnknownCustomer getInstance() { return INSTANCE; }

    private UnknownCustomer() { super("unknown"); }

    @Override
    public void charge(double amount) {
        // do nothing
    }
}

class CustomerRepository {
    private final java.util.Map<Integer, String> database = new java.util.HashMap<>();

    public Customer findCustomer(int id) {
        return database.containsKey(id)
            ? new Customer(database.get(id))
            : UnknownCustomer.getInstance();
    }
}
```

## 9. Known production uses

**Java's `java.util.Collections.emptyList()`** is a special case for an
empty list. The method returns an immutable empty list that implements
the `List` interface but throws `UnsupportedOperationException` on
mutation methods and returns 0 for `size()`. The Java documentation
states that the returned list is immutable and serialisable
([Collections.emptyList documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#emptyList()),
verified 2026-08-13). This is the special case pattern applied to the
empty list: instead of returning null and forcing a null check, return an
empty list that every caller can iterate safely.

**Python's `collections.defaultdict`** uses a special case for missing
keys. When a key is not found, `defaultdict` calls the default factory
function to produce a value, rather than raising `KeyError`. The Python
documentation states that the factory function is called with no
arguments and the return value is used as the value for the missing key
([collections.defaultdict documentation](https://docs.python.org/3/library/collections.html#collections.defaultdict),
verified 2026-08-13). This is the special case pattern applied to
missing dictionary entries.

## 10. Consequences

Positive.

- Null checks are eliminated from every call site, which removes
  boilerplate and the risk of forgetting the check.
- The special case object handles every call gracefully, which prevents
  null pointer errors.
- The special case is a named class, which communicates the concept of
  the unknown or default case in the code.
- The special case can evolve over time, gaining behaviour that is
  specific to the unknown case, for example logging or metrics.

Negative.

- The special case is a new class, which adds to the codebase's class
  count.
- The transparency of the special case can hide the fact that the caller
  is dealing with an unknown case, which may produce wrong results if
  the do nothing behaviour is not correct for a specific call site.
- The special case must implement every method of the interface, which is
  a maintenance burden when the interface changes.
- The special case may mask bugs: a caller that expected a real customer
  and got an unknown customer does not fail, it silently does nothing,
  which may be worse than a crash if the silence hides a real problem.

## 11. Failure modes and misuse

**Special case that hides a bug.** The special case silently does nothing
where the caller expected a real object, and the do nothing behaviour
masks a programming error. The symptom is a function that produces no
output and no error, because every call was a no op on the special case.

**Special case with wrong behaviour.** The special case's do nothing
behaviour is wrong for some call sites, and the caller needed to handle
the case differently. The symptom is incorrect behaviour at call sites
that were forced into the same do nothing behaviour.

**Special case that is too transparent.** The special case is so
transparent that the caller never knows it is dealing with a special
case, and debugging becomes harder because the caller cannot distinguish
a real object from a special case. The symptom is a debugger session
where the caller is operating on an unknown customer and does not realise
it.

**Over application.** Every nullable value gets a special case, producing
a constellation of empty classes that are each used once. The symptom is
a codebase with an `UnknownX` class for every `X`, most of which are
never returned, which is over engineering.

## 12. Trade-off matrix

| Alternative | Null checks | Safety | Transparency | When to prefer |
|---|---|---|---|---|
| Introduce Special Case | Eliminated | High | High, caller does not know | Null check is same at every site |
| Optional type | Type level | High | Explicit | Language has Option/Result |
| Keep null checks | Present | Low if forgotten | Explicit | Few check sites, varying handling |
| Replace Conditional with Polymorphism | N/A | High | High | Conditional dispatches on type |

## 13. Related and incompatible patterns

**Change Reference to Value** (same catalog) is related when the special
case is a value object. Making the special case immutable gives it value
semantics, which is safe for sharing.

**Change Value to Reference** (same catalog) is related when the special
case is a singleton. Making the special case a reference object with one
instance saves memory and gives every reference the same identity.

**Extract Class** (same catalog) is the next step when the special case
gains behaviour that is complex enough to deserve its own class. The
special case is extracted from the general case into a separate class.

**Replace Conditional with Polymorphism** (same catalog) is related when
the null check is part of a conditional that dispatches on type. The
special case is the polymorphic variant for the null type.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a special case class
and replacing null returns with it. The steps are:

1. Identify the type that is frequently null checked.
2. Create a special case class that implements the same interface.
3. Implement do nothing or default behaviour for each method.
4. Change the function that returned null to return the special case.
5. Remove the null checks from every call site.
6. Run the test suite. Any failure means a call site relied on the null
   check for behaviour that the special case does not reproduce.

**Path out.** The refactoring is reversed by removing the special case
class and reintroducing null checks. The reverse is rarely applied,
because the special case is usually an improvement. It is applied when
the special case is masking bugs or when the call sites need to
distinguish the general case from the special case.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised a null checked code path should now exercise the
special case's do nothing behaviour and should pass without the null
check.

A new test should verify the special case's behaviour for each method,
confirming that it produces the expected do nothing or default result.
This test guards against a future change that alters the special case's
behaviour.

A test that checks the function returns the special case for a missing
input should verify that the returned object is an instance of the
special case class, which confirms the function is returning the special
case instead of null.

## 16. Observability signals

The refactoring does not change behaviour for the general case, so the
observable signal in production for general case inputs is nothing. The
one observable difference is for special case inputs: where the old code
would have produced a null check or a null pointer error, the new code
produces the special case's do nothing behaviour, which is silent. This
silence is the observability challenge: the special case may mask errors
that the null check would have surfaced. A metric or a log on the
special case's methods can provide visibility into how often the special
case is invoked, which is the signal that tells you how many inputs are
hitting the unknown path.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the special case
prevents null pointer errors that can be exploited for denial of service.
The do nothing behaviour is safer than a crash, because a crash can leak
information through the error message. The special case handles the
missing input gracefully, which is a positive security signal.

The privacy relevant case is that the special case can log or audit the
missing input, which provides visibility into how often unknown inputs
occur. This is a positive privacy signal if the logging is done with
appropriate data handling, and a negative signal if the logging captures
sensitive data.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Introduce Special Case."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 9, "Introduce Null Object."
- Martin Fowler, *Analysis Patterns*, Addison-Wesley, 1997, "Special
  Case."
- Bobby Woolf, *The Pattern Almanac 1998*, Addison-Wesley, 1998, "Null
  Object."
- Oracle, "Collections.emptyList,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#emptyList()](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#emptyList()),
  verified 2026-08-13.
- Python Software Foundation, "collections.defaultdict,"
  [https://docs.python.org/3/library/collections.html#collections.defaultdict](https://docs.python.org/3/library/collections.html#collections.defaultdict),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
