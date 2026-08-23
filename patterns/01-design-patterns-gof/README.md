# Family 01. Design Patterns

Origin. Gamma, Helm, Johnson, Vlissides 1994

26 entries, 267,812 words, 7 more planned, 33 total when the family is complete. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Chain of Responsibility](chain-of-responsibility.md) | canonical | 11,381 | A request arrives and there are several plausible things that might deal with it, the correct one depends on the request itself, and the code raising the request has no business ... |
| [Command](command.md) | canonical | 11,022 | An invoker needs to trigger work without knowing what the work is, who performs it, or when it will actually run. |
| [Interpreter](interpreter.md) | canonical | 12,160 | A system has to make a decision, a computation, or a selection whose rule is not known when the system is compiled. |
| [Iterator](iterator.md) | canonical | 11,672 | A client needs to visit every element of a collection, and the collection knows how it stores those elements while the client does not and should not. |
| [Mediator](mediator.md) | canonical | 11,878 | A set of objects has to cooperate, and every one of them needs to know something about the others in order to do its part. |
| [Memento](memento.md) | canonical | 11,628 | An object holds state that changes over time, and something outside that object needs the ability to put the state back the way it was. |
| [Observer](observer.md) | canonical | 13,321 | A piece of state changes, and an unknown number of other pieces of the system need to react. |
| [State](state.md) | canonical | 14,281 | An object behaves differently depending on a mode it is in, and every method that depends on that mode has grown the same conditional. |
| [Strategy](strategy.md) | canonical | 11,071 | An object does a piece of work in more than one way, and the choice of way is not a property of the object's identity. |
| [Template Method](template-method.md) | canonical | 12,033 | Two or more procedures do the same thing in the same order, and differ in a small number of steps in the middle. |
| [Visitor](visitor.md) | canonical | 12,082 | There is a data structure whose shape is stable and whose set of node types almost never changes, and there is a growing pile of operations over it, each of which needs to do ... |

## Creational

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Abstract Factory](abstract-factory.md) | canonical | 6,653 | You have several product types that must vary together. |
| [Builder](builder.md) | canonical | 6,755 | A type is expensive or awkward to construct because construction has several independent axes. |
| [Factory Method](factory-method.md) | canonical | 6,010 | A class does real work that involves an object it must create, and it cannot name the concrete class of that object at the point where the work is written. |
| [Prototype](prototype.md) | canonical | 7,511 | You have an object whose configuration is expensive, awkward, or impossible to reconstruct from a constructor call. |
| [Singleton](singleton.md) | contested | 9,217 | A resource exists once in the running process, and code scattered across the program needs to reach it without threading a reference through every call. |

## Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Adapter](adapter.md) | canonical | 11,688 | Two pieces of code need to work together and neither can be changed to match the other. |
| [Bridge](bridge.md) | canonical | 12,403 | A single class hierarchy is being asked to vary along two independent axes at once, and the class count is growing as the product of the two axis sizes rather than as their sum. |
| [Composite](composite.md) | canonical | 10,897 | There is a domain where a thing can be made of the same kind of thing, without limit, and client code has to operate over the whole structure without caring how deep it goes. |
| [Data Access Object](data-access-object.md) | canonical | 6,468 | Most real applications need to read and write persistent data at some point, and that data can live behind very different access mechanisms: a relational database reached through ... |
| [Decorator](decorator.md) | canonical | 14,044 | An object needs an extra responsibility, only sometimes, only for some instances, and the set of extra responsibilities keeps growing and keeps combining. |
| [Dependency Injection](dependency-injection.md) | canonical | 5,802 | Fowler's own running example names the problem precisely. |
| [Facade](facade.md) | canonical | 11,164 | A caller needs a small, ordinary result from a subsystem that is large, correct and unpleasant to talk to. |
| [Flyweight](flyweight.md) | canonical | 11,738 | A program needs a very large number of objects that are almost all the same, and the memory cost of representing each one separately is what is going to break it. |
| [Marker Interface](marker-interface.md) | contested | 5,201 | Sometimes a class needs to signal a capability or a semantic property to an external mechanism, most often the runtime or a framework, without adding any real behaviour of its own. |
| [Proxy](proxy.md) | canonical | 9,732 | Some object is expensive, remote, dangerous, or shared, and the code that wants to use it should not have to know that. |

## Planned

Named, not yet authored. Queued in [docs/AUTHORING-QUEUE.json](../../docs/AUTHORING-QUEUE.json), each one to be built to the same 18-dimension standard as the entries above before it is published.

- Extension Object
- Multiton
- Null Object
- Private Class Data
- Role Object
- Servant
- Twin

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
