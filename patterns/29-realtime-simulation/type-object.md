---
name: Type Object
slug: type-object
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Breed Pattern, Data-Driven Type]
first_described: "Robert Nystrom's Type Object chapter in Game Programming Patterns, in the book's own Behavioral Patterns part"
maturity: canonical
related: [object-pool]
incompatible_with: []
verified: 2026-08-23
---

# Type Object

## 1. Name, aliases, and lineage

A type object lets an object's kind be defined as data at runtime, held on a
single shared instance every object of that kind references, rather than as
a compiled subclass baked into the type system.

The clearest, directly verified source is Robert Nystrom's own chapter,
which this entry fetched directly (Nystrom, Robert, "Type Object," Game
Programming Patterns, https://gameprogrammingpatterns.com/type-object.html,
verified 2026-08-23). the chapter's own stated intent, quoted directly.
"Allow the flexible creation of new 'classes' by creating a single class,
each instance of which represents a different type of object" (Nystrom,
"Type Object," verified 2026-08-23). Nystrom's own book places the chapter
in its Behavioral Patterns part, confirmed via the book's own table of
contents (https://gameprogrammingpatterns.com/contents.html, verified
2026-08-23), a different part from this catalogue's own Object Pool, Dirty
Flag, and Spatial Partitioning entries, which the same table of contents
places in the book's Optimization Patterns part.

## 2. Problem and context

Nystrom's own text names the recompile-cycle cost directly, using a
monster-breed example. "adding new breeds means adding new code, and each
breed has to be compiled in as its own type" (Nystrom, "Type Object,"
verified 2026-08-23). the chapter's own numbered worked example makes the
cost concrete. get an email asking to change a troll's health, check out
and change the troll's own header file, recompile, check in, reply, and
repeat for every tuning pass a designer wants.

The fix, per the chapter's own text, is to stop subclassing per breed and
instead give every monster instance a reference to a shared breed object
holding the data that used to live in the subclass. "we could also
architect our code so that each monster has a breed. Instead of subclassing
Monster for each breed, we have a single Monster class and a single Breed
class" (Nystrom, "Type Object," verified 2026-08-23).

## 3. Forces

The chapter's own text names the direct trade both ways. "adding new
breeds means adding new code" versus a data file a designer can edit
without recompiling. once that trade is made, a second, more specific
tension appears between what the pattern makes easy and what it makes
hard. "it's very easy to use type objects to define type-specific data,
but hard to define type-specific behavior. If, for example, different
breeds of monster needed to use different AI algorithms, using this
pattern becomes more challenging" (Nystrom, "Type Object," verified
2026-08-23).

## 4. Applicability and non-applicability

The chapter's own When to Use It section names two conditions directly.
"you don't know what types you will need up front" and "you want to be
able to modify or add new types without having to recompile or change
code" (Nystrom, "Type Object," verified 2026-08-23).

A narrower, related caveat appears in the chapter's own Design Decisions
section rather than as a general non-applicability statement. when
deciding whether type objects themselves need inheritance, the chapter
recommends against adding it unless genuinely needed. "it's simple.
Simplest is often best. If you don't have a ton of data that needs sharing
between your type objects, why make things hard on yourself" (Nystrom,
"Type Object," verified 2026-08-23). this is narrower than a blanket
skip-the-pattern-entirely case, and this entry reports that distinction
directly rather than smoothing it into a broader non-applicability claim.

## 5. Structure

Nystrom's own text describes the mechanism directly. "define a type object
class and a typed object class. Each type object instance represents a
different logical type. Each typed object stores a reference to the type
object that describes its type" (Nystrom, "Type Object," verified
2026-08-23). instance-specific data, such as a monster's current health,
stays on the typed object. shared, per-kind data, such as a breed's base
health, lives once on the type object every instance of that kind
references.

## 6. ASCII structure diagram

```
  rejected shape, subclass per breed:

  Monster (base class)
     |
     +-- Troll : Monster    (own compiled subclass, own stats)
     +-- Dragon : Monster   (own compiled subclass, own stats)
     +-- Goblin : Monster   (own compiled subclass, own stats)

  type object shape:

  Monster instance 1 (a troll)   ---+
  Monster instance 2 (a troll)   ---+---> Breed "Troll"
  Monster instance 3 (a troll)   ---+        health: 48
                                              attack: 12

  Monster instance 4 (a dragon)  -------> Breed "Dragon"
                                              health: 200
                                              attack: 40

  adding a new breed = building a new Breed object at
  runtime or load time, never writing or compiling new code.
```

## 7. Dynamics

At runtime, a typed object's lookup of shared data goes through its own
type reference rather than through a vtable baked in at compile time. the
chapter's own Design Decisions section names the runtime hazard of letting
that reference change. "there's a fairly tight coupling between an object
and its type... If we allow the breed to change, we need to make sure that
the new type's requirements are met by the existing object. When we
change the type, we will probably need to execute some validation code to
make sure the object is now in a state that makes sense for the new type"
(Nystrom, "Type Object," verified 2026-08-23).

## 8. Implementation variants

Unity's own ScriptableObject system is a genuine, live-verified match to
the pattern's own core mechanism, though Unity's own docs never use the
term "type object" or cite Nystrom's book. "ScriptableObjects are not
attached to GameObjects as components but exist in the project as assets,
independent of GameObjects," and "a common use for ScriptableObjects is as
a container for shared data used by multiple objects at runtime, which can
reduce a project's memory usage by avoiding copies of values" (Unity
Technologies, "ScriptableObject," Unity Manual, verified 2026-08-23). this
is the same one-shared-instance-referenced-by-many pattern, though Unity's
own text frames the benefit as memory savings rather than the
organization-and-flexibility framing this entry's own dimension 13 shows
the book itself uses to distinguish Type Object from Flyweight, and this
entry did not find Unity's own docs explicitly contrasting ScriptableObject
against subclassing a MonoBehaviour for defining new kinds, so that
structural parallel is this entry's own reasoned inference from the
confirmed facts, not a sentence Unity states outright.

## 9. Known production uses

The chapter's own text names no production system directly, this entry
confirmed that absence on a full read of the chapter. Unity's own
ScriptableObject system from dimension 8 is the strongest live-verified
candidate this entry could confirm, reported honestly as this entry's own
cross-reference rather than a claim the book itself makes.

## 10. Consequences

The chapter's own text states the benefit directly. "we've essentially
lifted a portion of the type system out of the hard-coded class hierarchy
into data we can define at runtime" (Nystrom, "Type Object," verified
2026-08-23). the cost is stated with equal directness, in two parts. the
program now owns the lifetime of every type object itself. "we are now
responsible for managing not only our monsters in memory, but also their
types... we've freed ourselves from some of the limitations of the
compiler, but the cost is that we have to re-implement some of what it
used to be doing for us" (Nystrom, "Type Object," verified 2026-08-23), and
the type-specific-behavior cost already quoted in dimension 3.

## 11. Failure modes and misuse

This entry explicitly checked the full chapter for a "type of a type"
smell, a type object itself needing its own type, and confirmed it is not
discussed anywhere, reporting that absence directly rather than inventing
a warning the source does not make. the real, sourced hazard the chapter
does name is the type-mutability invariant violation from dimension 7,
changing an object's type without validating that the object's own current
state still makes sense under the new type's own assumptions.

## 12. Trade-off matrix

| Dimension | Type object | Subclass per kind |
|---|---|---|
| Adding a new kind | New data, no recompile, dimension 4 | New subclass, recompile every time, dimension 2 |
| Type-specific data | Easy, lives on the shared instance, dimension 3 | Easy, lives on the subclass |
| Type-specific behavior | Hard, no natural per-kind override slot, dimension 3 | Easy, override a virtual method |
| Lifetime management | The program's own job now, dimension 10 | The compiler and runtime handle it |
| Changing a kind at runtime | Possible, needs validation, dimension 7 | Not possible without replacing the object |
| Best fit | Unknown or designer-editable kinds, dimension 4 | A small, fixed, known-at-compile-time kind set |

## 13. Related and incompatible patterns

Nystrom's own See Also section names three related patterns directly,
transcribed in full. "the high-level problem this pattern addresses is
sharing data and behavior between several objects. Another pattern that
addresses the same problem in a different way is Prototype." "Type Object
is a close cousin to Flyweight. Both let you share data across instances.
With Flyweight, the intent is on saving memory... With the Type Object
pattern, the focus is on organization and flexibility." "there's a lot of
similarity between this pattern and the State pattern. Both patterns let
an object delegate part of what defines itself to another object... you
can look at that as having our Type Object serve double duty as a State
too" (Nystrom, "Type Object," verified 2026-08-23).

This entry explicitly checked whether the chapter names a bridge to
Component or Entity-Component-System and confirmed neither is present
anywhere in the chapter, so a catalogue entry assuming that bridge would
be inventing it. Inline, not in See Also, the chapter also references
Factory Method for the constructor discussion, Interpreter and Bytecode
for defining behavior fully in data, and Object Pool for controlling
type-object allocation.

## 14. Refactoring path in and out

The chapter's own motivation section is itself an explicit before-and-after
refactor narrative rather than a separate migration guide. per dimension
2, the pivot is replacing a subclass-per-kind hierarchy with a single
concrete class plus a shared type-object class, moving the per-kind data
that used to be compiled into each subclass onto instances of that shared
class instead. the chapter also covers the narrower case of changing an
existing object's type at runtime, per dimension 7, requiring the same
validation discipline. this entry did not find guidance on refactoring
back out of the pattern toward subclassing, and reports that absence
directly.

## 15. Testing and verification

This entry explicitly checked the full chapter for a discussed testing or
verification methodology and confirmed none exists, reporting that
absence directly rather than inventing one.

## 16. Observability signals

This entry explicitly checked the full chapter and confirmed no metric or
runtime signal is named anywhere, reporting that absence directly.

## 17. Security and privacy implications

This entry did not find the chapter addressing a security or privacy
concern, and this entry did not find a reasoned extension of the pattern's
own structure worth offering here either, since class-as-data delegation
does not present an obvious security-relevant angle distinct from the
pattern's own stated lifetime-management cost from dimension 10.

## 18. References

1. Nystrom, Robert, "Type Object," Game Programming Patterns,
   https://gameprogrammingpatterns.com/type-object.html, verified
   2026-08-23.
2. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
3. Unity Technologies, "ScriptableObject," Unity Manual, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of the type object pattern, a
shared Breed instance referenced by many Monster instances, following the
mechanism from dimension 5 and the runtime type-change validation from
dimension 7.

```typescript
interface Breed {
  name: string;
  baseHealth: number;
  attack: number;
}

class Monster {
  private currentHealth: number;

  constructor(private breed: Breed) {
    this.currentHealth = breed.baseHealth;
  }

  getBreedName(): string {
    return this.breed.name;
  }

  getAttack(): number {
    return this.breed.attack;
  }

  changeBreed(newBreed: Breed): void {
    if (this.currentHealth > newBreed.baseHealth) {
      throw new Error("current health exceeds the new breed's base health");
    }
    this.breed = newBreed;
  }
}
```

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Breed:
    name: str
    base_health: int
    attack: int


class Monster:
    def __init__(self, breed: Breed) -> None:
        self._breed = breed
        self._current_health = breed.base_health

    def breed_name(self) -> str:
        return self._breed.name

    def attack(self) -> int:
        return self._breed.attack

    def change_breed(self, new_breed: Breed) -> None:
        if self._current_health > new_breed.base_health:
            raise ValueError("current health exceeds the new breed's base health")
        self._breed = new_breed
```

```go
package typeobject

import "errors"

type Breed struct {
	Name       string
	BaseHealth int
	Attack     int
}

type Monster struct {
	breed         *Breed
	currentHealth int
}

func NewMonster(breed *Breed) *Monster {
	return &Monster{breed: breed, currentHealth: breed.BaseHealth}
}

func (m *Monster) BreedName() string {
	return m.breed.Name
}

func (m *Monster) Attack() int {
	return m.breed.Attack
}

func (m *Monster) ChangeBreed(newBreed *Breed) error {
	if m.currentHealth > newBreed.BaseHealth {
		return errors.New("current health exceeds the new breed's base health")
	}
	m.breed = newBreed
	return nil
}
```
