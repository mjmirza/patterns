---
name: Extract Function
slug: extract-function
family: 03-refactoring
category: Refactoring
aliases: [Extract Method, Introduce Named Function, Name a Block]
first_described: "Fowler 1999"
maturity: canonical
related: [inline-function, extract-class, extract-variable, decompose-conditional, combine-functions-into-transform]
incompatible_with: []
verified: 2026-08-13
---

# Extract Function

## 1. Name, aliases, and lineage

The canonical name is **Extract Function**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 6, "Composing Methods," where it appeared
as **Extract Method**, the most frequently used refactoring in the
catalog. In the second edition, Martin Fowler, *Refactoring. Improving
the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter
6, "A First Set of Refactorings," Fowler renamed it to Extract Function
to reflect that the operation applies to free functions as well as
methods, which is important in JavaScript, Python, and other languages
where functions are not attached to classes.

The underlying idea, that a block of code with a clear purpose should be
named so its purpose is visible at the call site, is the oldest idea in
structured programming. Gerald Weinberg, in *The Psychology of Computer
Programming*, Van Nostrand Reinhold, 1971, described the practice of
naming blocks of code to improve readability. Kent Beck, in *Smalltalk
Best Practice Patterns*, Prentice Hall, 1997, formalised it as the
Composed Method pattern, which states that every method should do one
thing and should be named for what it does.

The alias **Extract Method** is the original name from the first edition
and is the name used in the Eclipse and IntelliJ refactoring menus, in
the Java and C sharp communities, and in most static analysis tools that
detect extraction opportunities.

## 2. Problem and context

You have a function that does two or more things, or a function that does
one thing but is long enough that a reader cannot hold the whole function
in their head. The function's name communicates what it does at a high
level, but the internals are a sequence of steps that each deserve a name,
and the names are absent because the steps are inline. A reader who wants
to understand one step must read and parse the code for that step, and a
reader who wants to understand the function at a high level must read past
the implementation details of every step.

The situation reads like this. A function called `printOwing` prints an
invoice. It first prints a banner, then computes the outstanding amount,
then prints the details. The function is forty lines long, and the three
steps are inline. A reader who wants to know what the banner looks like
must read the first ten lines, which are print statements. A reader who
wants to know how the outstanding amount is calculated must read the next
fifteen lines, which are arithmetic. A reader who wants to understand the
function at a high level must read all forty lines, because the structure
is not visible in the names, only in the code.

The fix is to extract each step into its own named function. `printBanner`
is one function, `getOutstanding` is another, and `printDetails` is a
third. `printOwing` becomes three calls, and each step is named. A reader
who wants to understand the high level reads the three call sites. A
reader who wants to understand a step reads the extracted function.

## 3. Forces

**Naming versus inlining.** An extracted function has a name, which
communicates intent at the call site. An inline block has no name, which
means the reader must read the code to understand the intent. The force
favours extraction when the block has a clear purpose that a name can
communicate, and favours inlining when the block is so simple that a name
would add indirection without clarity.

**Readability versus indirection.** An extracted function reads as a call
site that names each step, which is readable at the high level. A reader
who wants the implementation must navigate to the extracted function,
which is indirection. The force favours extraction when the high level
readability benefit exceeds the navigation cost, which happens when the
function is long enough that the high level is lost in the details.

**Reusability versus scope.** An extracted function can be called from
other places, which enables reuse. An inline block cannot be called from
other places, which prevents reuse but also prevents accidental coupling.
The force favours extraction when the block would benefit from reuse, and
favours inlining when the block is specific to one call site and should not
be reused.

**Testability versus integration.** An extracted function can be tested
in isolation, which is granular. An inline block can only be tested through
the enclosing function, which is integration. The force favours extraction
when testing the block independently is more valuable than testing the
integration.

**Variable scope versus parameter passing.** An inline block has access
to every local variable of the enclosing function. An extracted function
must receive its inputs as parameters, which is more explicit but also
more verbose. The force favours inlining when the block uses many local
variables and the parameter list would be long, and favours extraction when
the block uses few variables and the parameter list is short.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A function is long enough that a reader cannot understand it at a
  glance, and it has identifiable steps that each deserve a name.
- A block of code has a clear purpose that is not communicated by the
  surrounding code, and a name would make the purpose visible.
- A block of code is duplicated, and extracting it into a named function
  would allow both call sites to share the same implementation.
- A block of code is tested through the enclosing function only, and
  testing it in isolation would produce better failure messages.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The block is one or two lines, and its purpose is obvious from the code
  itself. Extracting it adds a function and a call site that are more
  ceremony than clarity.
- The block uses many local variables of the enclosing function, and the
  parameter list of the extracted function would be longer than the block
  itself. The parameter passing overhead exceeds the naming benefit.
- The function is already short and has one clear purpose. Extracting
  further produces trivial functions that add indirection without clarity.
- The block is specific to one call site and should not be reused, and the
  enclosing function is short enough that the block is readable inline.

## 5. Structure

The refactoring has one participant.

- **The block.** A sequence of statements inside a function. After the
  refactoring, the block is a separate function, and the original function
  calls it at the point where the block was.

The invariant is that the extracted function produces the same result as
the inline block did, for every input and every state the enclosing
function's locals were in.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  function printOwing():              function printOwing():
    # banner                            printBanner()
    print("***************")           outstanding = getOutstanding()
    print("*  INVOICE    *")            printDetails(outstanding)
    print("***************")
    # compute outstanding            function printBanner():
    outstanding = 0                     print("***************")
    for e in expenses:                  print("*  INVOICE    *")
        outstanding += e.amount         print("***************")
    # details
    print(f"name: {name}")          function getOutstanding():
    print(f"owed: {outstanding}")        outstanding = 0
                                       for e in expenses:
                                           outstanding += e.amount
                                       return outstanding

                                   function printDetails(outstanding):
                                       print(f"name: {name}")
                                       print(f"owed: {outstanding}")
```

## 7. Dynamics

```
  t0  identify block with a clear purpose
       |
       v
  t1  create a new function named for what
       the block does (not how it does it)
       |
       v
  t2  copy the block into the new function
       |
       v
  t3  determine parameters:
       -- locals read by the block become parameters
       -- locals written by the block become return values
       |
       v
  t4  replace the block with a call to the new function
       -- pass the parameters
       -- use the return value if the block wrote a local
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the block is now a named function.
```

## 8. Implementation variants

**Extract to method.** The canonical variant in object oriented languages.
The block is extracted as a method on the same class, which gives it
access to the class's fields without passing them as parameters. This is
the variant Fowler described in the first edition as Extract Method.

**Extract to free function.** The variant Fowler renamed to Extract
Function in the second edition. The block is extracted as a free function
or a module level function, which is the natural form in JavaScript,
Python, and other languages where functions are not attached to classes.

**Extract to local function.** In languages that support nested
functions, such as Python and JavaScript, the block is extracted as a
function nested inside the enclosing function. The nested function has
access to the enclosing function's locals through closure, which avoids
parameter passing for variables the block reads.

**Extract to arrow function.** In JavaScript and TypeScript, the block can
be extracted as an arrow function assigned to a const, which is the
language's idiom for naming a block without the ceremony of a function
declaration.

```python
# Python: before (long function with inline blocks)

def print_owing(name: str, expenses: list) -> None:
    print("***************")
    print("*  INVOICE    *")
    print("***************")
    outstanding = sum(e["amount"] for e in expenses)
    print(f"name: {name}")
    print(f"owed: {outstanding}")

# Python: after (extracted functions)

def print_banner() -> None:
    print("***************")
    print("*  INVOICE    *")
    print("***************")

def get_outstanding(expenses: list) -> int:
    return sum(e["amount"] for e in expenses)

def print_details(name: str, outstanding: int) -> None:
    print(f"name: {name}")
    print(f"owed: {outstanding}")

def print_owing(name: str, expenses: list) -> None:
    print_banner()
    outstanding = get_outstanding(expenses)
    print_details(name, outstanding)
```

```typescript
interface Expense {
    amount: number;
}

// TypeScript: after (extracted arrow functions)

const printBanner = (): void => {
    console.log("***************");
    console.log("*  INVOICE    *");
    console.log("***************");
};

const getOutstanding = (expenses: Expense[]): number =>
    expenses.reduce((sum, e) => sum + e.amount, 0);

const printDetails = (name: string, outstanding: number): void => {
    console.log(`name: ${name}`);
    console.log(`owed: ${outstanding}`);
};

function printOwing(name: string, expenses: Expense[]): void {
    printBanner();
    const outstanding = getOutstanding(expenses);
    printDetails(name, outstanding);
}
```

```java
import java.util.List;

class Expense {
    int amount;
}

// Java: after (extracted methods on a class)

public class InvoicePrinter {
    private String name;
    private List<Expense> expenses;

    public void printOwing() {
        printBanner();
        int outstanding = getOutstanding();
        printDetails(outstanding);
    }

    private void printBanner() {
        System.out.println("***************");
        System.out.println("*  INVOICE    *");
        System.out.println("***************");
    }

    private int getOutstanding() {
        return expenses.stream().mapToInt(e -> e.amount).sum();
    }

    private void printDetails(int outstanding) {
        System.out.println("name: " + name);
        System.out.println("owed: " + outstanding);
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's "Extract Method" refactoring** is the most widely used
tool for this refactoring in the Java world. JetBrains documents that the
tool analyses the selected block, determines the parameters and the
return type, generates the method, and replaces the block with a call
([JetBrains Extract Method](https://www.jetbrains.com/help/idea/extract-method.html),
verified 2026-08-13). The tool handles the variable analysis that is the
mechanically hard part of the refactoring.

**Eclipse's "Extract Method" refactoring** provides the same automation.
The Eclipse documentation describes the tool as analysing the selection
for local variable reads and writes, generating a method with the
correct signature, and updating every call site
([Eclipse Extract Method](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-extract_method.htm),
verified 2026-08-13).

## 10. Consequences

Positive.

- The extracted function has a name, which communicates its purpose at
  the call site.
- The enclosing function reads as a sequence of named steps, which is
  readable at a high level without requiring the reader to parse
  implementation details.
- The extracted function can be tested in isolation, which produces more
  granular failure messages.
- The extracted function can be reused by other callers, which eliminates
  duplication.

Negative.

- The reader who wants the implementation must navigate to the extracted
  function, which adds indirection.
- The parameter list of the extracted function may be long if the block
  used many locals, which makes the call site verbose.
- The number of functions in the codebase increases, which adds navigation
  overhead.
- The extraction can be over applied, producing trivial functions that add
  indirection without clarity.

## 11. Failure modes and misuse

**Extracting a trivial block.** A one line block is extracted into a
function whose name is longer than the code itself. The function adds a
call and a definition that are more ceremony than clarity. The symptom is
a codebase full of one line functions that a reader must navigate through
to understand the simplest operations.

**Bad name.** The extracted function is named for how the block works
rather than for what the block does. A function called
`sumAndPrintExpenses` does not communicate the purpose as well as one
called `printInvoiceDetails`. The symptom is a function whose name must
be read alongside its body to understand what it does, which defeats the
purpose of the extraction.

**Parameter explosion.** The block uses many local variables, and the
extracted function takes ten parameters, each passed from the enclosing
function. The call site is longer than the original inline block, and the
extraction has added ceremony without clarity. The fix is to use
Introduce Parameter Object to group the parameters, or to extract the
block as a method on a class that holds the variables as fields.

**Side effect extraction.** The block modifies a local variable of the
enclosing function, and the extracted function returns the modified value,
but the caller forgets to use the return value. The symptom is a silent
logic error where the modification is lost, because the extracted function
made the modification locally but the caller did not capture the result.

## 12. Trade-off matrix

| Alternative | Naming | Indirection | Reusability | When to prefer |
|---|---|---|---|---|
| Extract Function | High, block has a name | One function call | High, can be called elsewhere | Block has a clear purpose, function is long |
| Inline Function | None, code is at call site | None | None | Function is trivial, name adds no value |
| Introduce Explaining Variable | High, variable has a name | One variable | None | Expression is complex, not a block |
| Extract Class | High, class has a name | New class | High, class can be reused | Two responsibilities need separation |

## 13. Related and incompatible patterns

**Inline Function** (same catalog) is the inverse. It replaces a function
call with the function's body at the call site. The two are applied in
opposite directions: Extract adds a function, Inline removes one. A
codebase that oscillates between them is not making a mistake, it is
responding to changing requirements about what should be named.

**Extract Class** (same catalog) is the larger scale version. It extracts
a group of fields and methods into a new class, where Extract Function
extracts a block into a new function. The two are complementary: Extract
Function is the building block of Extract Class, because the methods are
moved using Extract Function's mechanics.

**Extract Variable** (same catalog) is the expression level version. It
extracts a subexpression into a named variable, where Extract Function
extracts a block into a named function. The two are the two levels of
naming: expressions and blocks.

**Decompose Conditional** (same catalog) is a specific application of
Extract Function to the parts of a conditional. The condition, the then
branch, and the else branch are each extracted into a named function.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a new function and
moving the block into it. The steps are:

1. Identify the block with a clear purpose.
2. Create a new function named for what the block does.
3. Copy the block into the new function.
4. Determine the parameters: locals read by the block become parameters,
   locals written by the block become return values.
5. Replace the block in the original function with a call to the new
   function, passing the parameters and using the return value.
6. Run the test suite. Any failure means the parameters or the return
   value were not handled correctly.

**Path out.** The refactoring is reversed by Inline Function, which
replaces the function call with the function's body at the call site. The
reverse is applied when the function is trivial and the name adds no
value over the body itself.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the original function should produce the same result.
A test failure means the parameters or the return value were not handled
correctly, or a local variable was not passed.

A new test should test the extracted function in isolation, calling it
directly with known inputs and verifying the output. This test is more
granular than the integration test of the enclosing function and produces
better failure messages when a change breaks the extracted function.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in profiling,
where the extracted function appears as a separate entry in the profiler.
This is actually an observability improvement, because the profiler now
shows the cost of each step independently, where the inline block showed
only the aggregate cost of the enclosing function.

## 17. Security and privacy implications

The refactoring does not change what data is processed or how it is
processed, so it does not change the security surface. The security
relevant case is when the extracted function is a security check, for
example a validation or an authorisation check, and the name makes the
security boundary visible at the call site. A caller that sees
`validateInput(raw)` understands that validation is happening, where an
inline block might not make the security boundary visible.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Extract Function."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Extract Method."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
  "Composed Method" pattern.
- Gerald Weinberg, *The Psychology of Computer Programming*, Van Nostrand
  Reinhold, 1971.
- JetBrains, "Extract Method,"
  [https://www.jetbrains.com/help/idea/extract-method.html](https://www.jetbrains.com/help/idea/extract-method.html),
  verified 2026-08-13.
- Eclipse Foundation, "Extract Method,"
  [https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-extract_method.htm](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-extract_method.htm),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
