# Family 03. Refactoring Techniques

Origin. Fowler, Refactoring 2nd edition

32 entries, 86,433 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Refactoring

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Change Function Declaration](change-function-declaration.md) | canonical | 4,133 | A function's declaration, its name and its parameter list, is the single contract every caller depends on. |
| [Change Reference to Value](change-reference-to-value.md) | canonical | 3,516 | You have a reference object, an object whose identity matters and which is shared among multiple callers, but the sharing is producing more problems than it solves. |
| [Change Value to Reference](change-value-to-reference.md) | canonical | 3,616 | You have a value object, an object whose identity is defined by its field values and which is immutable, but the immutability and the value semantics are producing more problems ... |
| [Collapse Hierarchy](collapse-hierarchy.md) | canonical | 3,138 | A subclass and its superclass have diverged or, more commonly, have converged to the point where the hierarchy level adds no value. |
| [Combine Functions into Class](combine-functions-into-class.md) | canonical | 3,579 | You have a set of functions, typically free functions in a module, that all operate on the same data structure or the same set of parameters. |
| [Combine Functions into Transform](combine-functions-into-transform.md) | canonical | 3,278 | You have a pipeline of functions, each taking the output of the previous and producing input for the next, forming a chain of transformations. |
| [Consolidate Conditional Expression](consolidate-conditional-expression.md) | canonical | 3,243 | You have a series of conditional checks, each of which leads to the same result or the same action. |
| [Decompose Conditional](decompose-conditional.md) | canonical | 3,393 | You have a conditional whose complexity lies not in the branching but in the readability of its parts. |
| [Encapsulate Collection](encapsulate-collection.md) | canonical | 3,249 | A class has a collection field, typically a list or a map, that is exposed to callers. |
| [Encapsulate Record](encapsulate-record.md) | canonical | 3,025 | You have a data record, a structure with public fields and no behaviour, that callers read and write directly. |
| [Encapsulate Variable](encapsulate-variable.md) | canonical | 3,123 | You have a variable, typically a public field on a class or a module level variable, that callers read and write directly. |
| [Extract Class](extract-class.md) | canonical | 3,113 | You have a class that has grown to the point where it does two things that should be separate. |
| [Extract Function](extract-function.md) | canonical | 3,043 | You have a function that does two or more things, or a function that does one thing but is long enough that a reader cannot hold the whole function in their head. |
| [Extract Superclass](extract-superclass.md) | canonical | 2,825 | You have two classes that share fields and methods, either because they were written independently and converged, or because they were originally one class that was split and the ... |
| [Extract Variable](extract-variable.md) | canonical | 2,799 | You have an expression that is hard to read because it combines several subexpressions into one statement. |
| [Hide Delegate](hide-delegate.md) | canonical | 2,863 | A client calls a method on an object it reaches through another object, forming a chain of access. |
| [Inline Class](inline-class.md) | canonical | 2,513 | You have a class that no longer earns its place. |
| [Inline Function](inline-function.md) | canonical | 2,528 | You have a function whose body is as clear as its name, or clearer. |
| [Inline Variable](inline-variable.md) | canonical | 2,113 | You have a variable whose initialiser is as clear as the variable name, or clearer. |
| [Introduce Assertion](introduce-assertion.md) | canonical | 2,657 | A section of code makes an assumption about the state of the program at that point, for example that a divisor is not zero, that a list is not empty, or that a temperature is in a ... |
| [Introduce Parameter Object](introduce-parameter-object.md) | canonical | 2,642 | You have a function with a long parameter list where several parameters are naturally related. |
| [Introduce Special Case](introduce-special-case.md) | canonical | 3,021 | You have code that checks for null, or for a special value that means "no value" or "unknown," before every operation on the object. |
| [Move Field](move-field.md) | canonical | 2,268 | A field is on a class that does not use it, or that uses it less than another class does. |
| [Move Function](move-function.md) | canonical | 2,436 | A function is on a class or module that does not use it, or that uses it less than another class does. |
| [Move Statements into Function](move-statements-into-function.md) | canonical | 1,717 | You have a function that is called from multiple places, and every caller performs the same statements immediately before or after the call. |
| [Move Statements to Callers](move-statements-to-callers.md) | canonical | 1,599 | A function performs statements that vary by caller or that are not the function's responsibility. |
| [Parameterize Function](parameterize-function.md) | canonical | 1,755 | You have two or more functions that perform the same operation with different constant values. |
| [Preserve Whole Object](preserve-whole-object.md) | canonical | 2,026 | A function takes several parameters that are all fields of the same object. |
| [Pull Up Constructor Body](pull-up-constructor-body.md) | canonical | 1,881 | Two or more subclasses have constructors that share the same initialisation logic. |
| [Pull Up Field](pull-up-field.md) | canonical | 1,774 | Two or more subclasses have the same field, with the same type and the same meaning. |
| [Pull Up Method](pull-up-method.md) | canonical | 1,714 | Two or more subclasses have the same method, with the same body and the same signature. |
| [Push Down Field](push-down-field.md) | canonical | 1,853 | A field on the superclass is only used by one subclass. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
