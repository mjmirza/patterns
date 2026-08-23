---
name: Composite Entity
slug: composite-entity
family: 06-enterprise-application-architecture
category: Enterprise Application Architecture
aliases: [Composite Entity BMP, Composite Transfer Object Strategy]
first_described: "Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4"
maturity: established
related: [data-transfer-object]
incompatible_with: []
verified: 2026-08-23
---

# Composite Entity

## 1. Name, aliases, and lineage

A Composite Entity aggregates a set of related domain objects into one
coarse-grained persistent unit, so a network of fine-grained related
objects is not each mapped to its own remote, individually addressable
persistent component.

This entry sources it directly from the corejeepatterns.com companion
site to the book that named it, retrieved live from the Internet
Archive's Wayback Machine after the site's own live hosting stopped
resolving. "you want to use entity beans to implement your conceptual
domain model" is the pattern's own stated Problem, verbatim (Deepak Alur,
John Crupi, Dan Malks, "Composite Entity," Core J2EE Patterns companion
site, archived snapshot,
https://web.archive.org/web/20211229230824/http://corej2eepatterns.com/CompositeEntity.htm,
archived 29 December 2021, verified 2026-08-23, excerpted from Core J2EE
Patterns, 2nd Edition, Prentice Hall, 2003).

## 2. Problem and context

A domain model made of many small, related objects, mapped one-to-one to
individually remote, individually persistent components, pays a real
network and management cost for every one of those fine-grained pieces,
which the archived source names directly as one of its own central
forces under dimension 3.

## 3. Forces

The archived source names six forces directly, verbatim. "you want to
avoid the drawbacks of remote entity beans, such as network overhead and
remote inter-entity bean relationships," "you want to [use]
bean-managed persistence (BMP) using custom or legacy persistence
implementations," "you want to implement parent-child relationships
efficiently when implementing Business Objects as entity beans," "you
want to encapsulate and aggregate existing POJO Business Objects with
entity beans," "you want to [use] EJB container transaction management
and security features," and "you want to encapsulate the physical
database design from the clients" (Alur, Crupi, Malks, "Composite
Entity," verified 2026-08-23).

## 4. Applicability and non-applicability

The archived source names its own Consequences directly, quoted in full
under dimension 10, including "increases object granularity" as a
directly named trade-off, so the pattern's own coarse-grained aggregation
is a deliberate choice against a genuinely fine-grained domain model where
each individual piece truly needs to be addressed, secured, or transacted
against on its own.

## 5. Structure

The archived source's own stated Solution names the structural shape
directly. "use a Composite Entity to implement persistent Business
Objects using local entity beans and POJOs. Composite Entity aggregates a
set of related Business Objects into coarse-grained entity bean
implementations" (Alur, Crupi, Malks, "Composite Entity," verified
2026-08-23).

## 6. ASCII structure diagram

```
  +---------------------------------------------+
  | Composite Entity, one coarse-grained unit       |
  |                                                 |
  |   +------------+   +------------+   +---------+ |
  |   | Business    |   | Business    |   | POJO      | |
  |   | Object A    |   | Object B    |   | child     | |
  |   +------------+   +------------+   +---------+ |
  +---------------------------------------------+

  the aggregate, not each individual part, is what a client addresses,
  per dimension 5
```

## 7. Dynamics

The archived source names two concrete BMP-level runtime strategies
directly, already listed under dimension 8. "Lazy Loading Strategy" and
"Store Optimization (Dirty Marker) Strategy" (Alur, Crupi, Malks,
"Composite Entity," verified 2026-08-23), naming the runtime discipline of
loading only the parts of the aggregate actually needed, and of writing
back to the underlying store only the parts that actually changed.

## 8. Implementation variants

The archived source names three named strategy groups directly. "Composite
Entity Remote Facade Strategy," "Composite Entity BMP Strategies" (itself
naming "Lazy Loading Strategy" and "Store Optimization (Dirty Marker)
Strategy" as its own sub-variants, per dimension 7), and "Composite
Transfer Object Strategy" (Alur, Crupi, Malks, "Composite Entity,"
verified 2026-08-23).

## 9. Known production uses

The pattern is documented as one of the named business-tier patterns
listed in the same source's own site navigation, alongside Business
Delegate, Service Locator, Session Facade, Application Service, and
Business Object (Alur, Crupi, Malks, "Composite Entity," Core J2EE
Patterns companion site, archived snapshot,
https://web.archive.org/web/20211229230824/http://corej2eepatterns.com/CompositeEntity.htm,
verified 2026-08-23), the reference catalogue for the J2EE platform's own
enterprise application architecture, per dimension 1.

## 10. Consequences

The archived source names its own Consequences directly, verbatim, as a
list. "increases maintainability," "improves network performance,"
"reduces database schema dependency," "increases object granularity,"
and "facilitates composite transfer object creation" (Alur, Crupi, Malks,
"Composite Entity," verified 2026-08-23), naming both the direct benefits
and the named trade-off, increased granularity of the aggregate itself,
in the same list.

## 11. Failure modes and misuse

The source's own directly named distinction from a sibling assembly
pattern, already partly quoted under dimension 13, is the sharpest
directly sourced risk of misuse. treating a Composite Entity as
interchangeable with a Transfer Object Assembler misapplies the wrong
one, since the archived source states the data sources differ, all parts
of a Composite Entity's own aggregate versus potentially many independent
entity beans, session beans, and Data Access Objects for a Transfer
Object Assembler.

## 12. Trade-off matrix

| Dimension | With a Composite Entity | One entity bean per fine-grained object |
|---|---|---|
| Network overhead per remote call | Reduced, one coarse-grained call, dimension 2 and 3 | High, one call per fine-grained piece |
| Object granularity | Coarser, named trade-off, dimension 4 and 10 | Fine-grained, addressed individually |
| Persistence strategy flexibility | Custom or legacy BMP, dimension 3 | Container-managed, less custom control |
| Database schema coupling to clients | Reduced, dimension 10 | Higher, schema shape leaks through |

## 13. Related and incompatible patterns

This entry cross-references this catalogue's own already published Data
Transfer Object entry directly, per the archived source's own directly
stated relationship. "the Composite Entity creates a composite Transfer
Object and returns it to the client. The Transfer Object is used to carry
data from the Composite Entity and its dependent objects" (Alur, Crupi,
Malks, "Composite Entity," verified 2026-08-23), and reports honestly
that the archived source's own named Transfer Object Assembler and
Business Object relationships, discussed in the same Related Patterns
section, are not yet published entries in this catalogue to cross-
reference directly.

## 14. Refactoring path in and out

The archived source names the concrete lever for adopting this pattern
directly, already quoted in dimension 5, aggregating a set of related
Business Objects into one coarse-grained entity bean rather than mapping
each one to its own remote entity bean. The reverse lever, implied
directly by the source's own named increased-granularity trade-off under
dimension 4, 10, and 12, is splitting the aggregate back into individually
addressable pieces once a genuine need to address, secure, or transact
against them independently emerges.

## 15. Testing and verification

This entry explicitly checked the fetched source for a documented test
methodology specific to this pattern and did not find one described as a
formal process on the archived page. the closest verifiable behavior is
the named Store Optimization (Dirty Marker) Strategy under dimension 7
and 8, which a test would exercise by confirming only the parts of the
aggregate that were actually mutated are written back to the underlying
store on save, not the whole aggregate unconditionally.

## 16. Observability signals

This entry explicitly checked the fetched source for a named metric or
dashboard specific to this pattern and did not find one described on the
archived page. the closest directly sourced signal is the named Lazy
Loading Strategy under dimension 7 and 8, which an operator could
instrument to confirm which parts of a large aggregate are actually being
loaded on a given access path, versus loaded and never used.

## 17. Security and privacy implications

The archived source names EJB container security features directly under
dimension 3, "you want to [use] EJB container transaction management
and security features," naming the aggregate's coarse-grained boundary as
the level at which the container's own security and transaction controls
apply.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, "Composite Entity," Core J2EE
   Patterns companion site, archived snapshot,
   https://web.archive.org/web/20211229230824/http://corej2eepatterns.com/CompositeEntity.htm,
   archived 29 December 2021, verified 2026-08-23. Excerpted from Core
   J2EE Patterns, 2nd Edition, Prentice Hall, 2003, ISBN 0-13-142246-4.

## Code

TypeScript, Python, and Go implementations of a minimal Composite Entity
following the mechanism from dimensions 5, 7, and 8, aggregating related
child objects behind one coarse-grained unit and writing back only the
parts that changed.

```typescript
interface ChildObject {
  id: string;
  value: string;
  dirty: boolean;
}

class CompositeEntity {
  private children: Map<string, ChildObject> = new Map();

  setChild(id: string, value: string): void {
    this.children.set(id, { id, value, dirty: true });
  }

  save(store: Map<string, string>): void {
    for (const child of this.children.values()) {
      if (child.dirty) {
        store.set(child.id, child.value);
        child.dirty = false;
      }
    }
  }
}
```

```python
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ChildObject:
    id: str
    value: str
    dirty: bool = True


class CompositeEntity:
    def __init__(self) -> None:
        self._children: Dict[str, ChildObject] = {}

    def set_child(self, child_id: str, value: str) -> None:
        self._children[child_id] = ChildObject(id=child_id, value=value, dirty=True)

    def save(self, store: Dict[str, str]) -> None:
        for child in self._children.values():
            if child.dirty:
                store[child.id] = child.value
                child.dirty = False
```

```go
package compositeentity

type ChildObject struct {
	ID    string
	Value string
	Dirty bool
}

type CompositeEntity struct {
	children map[string]*ChildObject
}

func NewCompositeEntity() *CompositeEntity {
	return &CompositeEntity{children: make(map[string]*ChildObject)}
}

func (c *CompositeEntity) SetChild(id string, value string) {
	c.children[id] = &ChildObject{ID: id, Value: value, Dirty: true}
}

func (c *CompositeEntity) Save(store map[string]string) {
	for _, child := range c.children {
		if child.Dirty {
			store[child.ID] = child.Value
			child.Dirty = false
		}
	}
}
```
