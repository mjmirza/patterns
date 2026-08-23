# Family 02. Code Smells

Origin. Fowler and Beck, Refactoring

28 entries, 221,162 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Bloaters

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Data Clumps](data-clumps.md) | canonical | 5,832 | The smell shows up first in method signatures. |
| [Duplicate Code](duplicate-code.md) | canonical | 8,029 | The same idea is written down twice, or more, in a codebase, so that changing the idea means finding and editing every copy. |
| [Large Class](large-class.md) | canonical | 9,844 | A class keeps absorbing new fields and new methods until it is doing the job of what should have been five or six separate collaborators. |
| [Lazy Class](lazy-class.md) | canonical | 7,708 | A codebase accretes classes over time for reasons that have nothing to do with present-day need. |
| [Long Method](long-method.md) | canonical | 7,675 | A method starts small. It does one clear thing, and its name says what that thing is. |

## Change Preventers

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Divergent Change](divergent-change.md) | canonical | 7,488 | A single class keeps needing edits, and the edits have nothing to do with each other. |
| [Mutable Data](mutable-data.md) | canonical | 6,860 | A piece of mutable data becomes a smell the moment two conditions hold at once. |
| [Parallel Inheritance Hierarchies](parallel-inheritance-hierarchies.md) | canonical | 6,677 | The smell appears whenever a codebase has two or more class hierarchies where subclassing one forces a matching subclass to be added to the other, over and over, for as long as ... |

## Code Smell

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Comments](comments.md) | canonical | 8,795 | A comment is a message from one point in time to a later reader, and it is never checked by anything that runs. |
| [Dead Code](dead-code.md) | canonical | 9,473 | Dead code accumulates as an ordinary, unavoidable byproduct of change. |
| [Long Parameter List](long-parameter-list.md) | canonical | 7,502 | A function, method, or constructor accumulates parameters over its lifetime, usually one at a time, usually each addition individually reasonable, until the call site becomes ... |
| [Loops](loops.md) | canonical | 8,826 | A loop is the most flexible construct available in an imperative language. |
| [Middle Man](middle-man.md) | canonical | 7,237 | The smell shows up during evolution, almost never at the moment a class is first written. |
| [Primitive Obsession](primitive-obsession.md) | canonical | 7,365 | A codebase represents a concept from its domain, a monetary amount, a telephone number, a temperature, an email address, a percentage, a date range, a currency code, using the ... |

## Code Smell, Object-Oriented Abusers

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Alternative Classes with Different Interfaces](alternative-classes-with-different-interfaces.md) | canonical | 8,373 | Two classes exist in the same codebase that do, in substance, the same job. |

## Coupling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Feature Envy](feature-envy.md) | canonical | 7,482 | A method sits on class A. Most of its logic reads or computes from the fields and accessor methods of class B, an object it was handed as a parameter, an instance variable, or ... |
| [Global Data](global-data.md) | canonical | 7,870 | A program needs some piece of information in more than one place. |
| [Inappropriate Intimacy](inappropriate-intimacy.md) | canonical | 8,379 | Two classes end up knowing far more about each other's insides than either one's public contract admits to. |
| [Incomplete Library Class](incomplete-library-class.md) | canonical | 8,434 | A team depends on a class, module, or type that ships from outside the codebase they control. |
| [Insider Trading](insider-trading.md) | canonical | 8,077 | Two modules were designed to talk to each other through a small, deliberate interface, and over time they grew a second, informal interface nobody designed. |
| [Message Chains](message-chains.md) | canonical | 6,586 | A client asks one object for a second object, then immediately asks that second object for a third, and continues down the line until it finally reads or calls the field it ... |
| [Shotgun Surgery](shotgun-surgery.md) | canonical | 7,839 | A team ships a single logical concept, adding a new payment method, adding a new shipping carrier, adding a new order status, renaming a field that a dozen call sites read. |

## Object-Orientation Abusers

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Data Class](data-class.md) | canonical | 7,208 | A class is created to represent something, usually because a database table, an external API payload, or a domain noun needs a type. |
| [Refused Bequest](refused-bequest.md) | canonical | 9,224 | The smell shows up the moment someone writes a subclass that extends a base class not because the subclass genuinely wants to honor the base class's whole public contract, but ... |
| [Repeated Switches](repeated-switches.md) | canonical | 7,719 | A codebase accumulates a type code, an enum, a string discriminant, or a kind field on a tagged union, that represents a small closed family of variants a business actually cares ... |
| [Switch Statements](switch-statements.md) | canonical | 8,919 | The problem starts small and grows by exactly the mechanism the smell is named for, switching. |
| [Temporary Field](temporary-field.md) | canonical | 9,243 | The smell appears when a class has a method that implements a complex, multi-step algorithm, and that algorithm needs several intermediate values threaded through more than one ... |

## Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Speculative Generality](speculative-generality.md) | canonical | 6,498 | The smell shows up at the moment a developer, while building the one feature actually requested, imagines a family of features that might follow it and builds the software to ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
