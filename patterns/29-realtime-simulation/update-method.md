---
name: Update Method
slug: update-method
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Tick Method, Per-Frame Update, Frame Slicing]
first_described: "Robert Nystrom's Update Method chapter in Game Programming Patterns, in the book's own Sequencing Patterns part"
maturity: canonical
related: [game-loop]
incompatible_with: []
verified: 2026-08-23
---

# Update Method

## 1. Name, aliases, and lineage

The update method pattern gives each object in a simulation its own
update() method, called once per frame by the game loop's own per-frame
walk over the collection, so each object's behaviour stays self-contained
rather than being hardcoded into a single central dispatcher.

The clearest, directly verified source is Robert Nystrom's own chapter,
which this entry fetched directly and confirmed both its stated intent and
its own section structure (Nystrom, Robert, "Update Method," Game
Programming Patterns, https://gameprogrammingpatterns.com/update-method.html,
verified 2026-08-23). the chapter's own stated intent, quoted directly.
"Simulate a collection of independent objects by telling each to process
one frame of behavior at a time" (Nystrom, "Update Method," verified
2026-08-23). the page itself is organized, in order, as Intent, Motivation,
The Pattern, When to Use It, Keep in Mind, Sample Code, Design Decisions,
and See Also, confirmed via a dedicated structure-only fetch of the same
page. Nystrom's own book places the chapter in its Sequencing Patterns
part, alongside this catalogue's own Game Loop entry, confirmed via the
book's own table of contents (verified 2026-08-23).

## 2. Problem and context

Nystrom's own chapter opens with a directly quoted motivating example. a
skeleton on patrol, whose per-frame behaviour, moving toward the next
patrol point, playing an animation, checking for the player, starts as its
own small piece of code, then a second skeleton is added, then a third, and
"pretty soon, you have a big blob of code" where "the skeleton-patrolling
code and the statue-toppling code and the ghost-flying code are all mushed
together" in one place (Nystrom, "Update Method," verified 2026-08-23). the
naive fix, one giant function handling every object kind's per-frame logic
in a single branch, is what the pattern exists to avoid.

The chapter's own stated fix is direct. give each object a single method,
`update()`, that "the game world calls... on every object in the game loop,
once per frame. This gives each object a chance to do its thing," and the
game loop itself becomes a simple, uniform walk over a collection, calling
that one method on every entry rather than knowing anything about what each
object actually does (Nystrom, "Update Method," verified 2026-08-23). this
is the same per-frame cadence this catalogue's own Game Loop entry
establishes, and this pattern is the piece that connects that cadence to
each individual simulated object.

## 3. Forces

The chapter's own text names the direct tension. one loop, one uniform
cadence, calling every object's own logic, versus every object kind needing
genuinely different per-frame behaviour. the pattern resolves it by pushing
all of the variation behind one identical method signature, so the loop
itself stays "dumb," walking the collection and calling `update()`, while
each concrete object decides what its own turn actually does (Nystrom,
"Update Method," verified 2026-08-23).

A second, more structural tension is between the collection driving the
iteration and the objects themselves being able to change that same
collection mid-iteration, spawning a new object or removing themselves, a
tension the chapter's own Keep in Mind section names directly and this
entry's own dimension 7 and dimension 11 cover at length. safe iteration
and self-modifying membership are, per the source, genuinely in tension,
and the pattern does not resolve it for free, it is a hazard the calling
code must still handle correctly.

## 4. Applicability and non-applicability

The pattern applies to any simulation holding a collection of independent
objects that each need their own per-frame behaviour driven by one uniform
outer loop, the chapter's own stated intent from dimension 1. games are
the chapter's own domain, but the same shape, a fixed, per-tick callback
invoked uniformly across a heterogeneous collection, appears directly in
Akka's own actor model documentation, "an actor is a container for state,
behavior, a mailbox, child actors and a supervisor strategy... an actor
processes one message at a time" (Akka, "Actor Systems," verified
2026-08-23), a genuine, sourced non-game match this entry's own dimension 9
covers directly.

The pattern is a poor fit when objects genuinely have no independent
per-frame behaviour, a purely reactive, event-driven system with nothing
to advance on a clock tick gains nothing from an `update()` call that would
do nothing most frames. this entry did not find the source stating this
non-applicable case explicitly, reporting it as this entry's own reasoned
inference from the pattern's own stated intent, per dimension 1, rather
than a directly sourced claim.

## 5. Structure

Nystrom's own text describes the mechanism directly. a common base type,
in the chapter's own terms an "Entity" or "GameObject," exposes a single
`update()` method that every concrete subclass overrides with its own
behaviour, and the surrounding game loop, from this catalogue's own Game
Loop entry, holds a collection of these objects and calls `update()` on
each one, once, every frame (Nystrom, "Update Method," verified 2026-08-23).
the loop itself never inspects what kind of object it is calling, it only
knows every entry in the collection answers to the same one method.

The chapter's own Design Decisions section names a further structural
choice with a real trade-off. how much control the object's own `update()`
call has over its per-frame timestep, whether it receives a fixed or
variable elapsed time, the same fixed-versus-variable-step choice this
catalogue's own Game Loop entry covers in depth, since the update method is
where that choice is actually felt by the object's own code (Nystrom,
"Update Method," verified 2026-08-23).

## 6. ASCII structure diagram

```
  game loop, once per frame (this catalogue's own Game Loop entry):

  for each object in the collection:
       |
       v
  object.update(deltaTime)
       |
       +-- skeleton.update() -> patrol logic, own state
       +-- statue.update()   -> topple logic, own state
       +-- ghost.update()    -> fly logic, own state

  the loop never branches on object kind.
  every object answers to the same one method.

  the hazard, dimension 7 and dimension 11:

  for each object in the collection:     <- iterating
       |
       object.update()  -----> may ADD a new object to this
                                same collection, or REMOVE
                                itself from it, mid-iteration
```

## 7. Dynamics

Nystrom's own Keep in Mind section names the runtime hazard directly, under
its own heading, "Be careful modifying the object list while updating." the
collection being iterated is the same collection an object's own `update()`
call can mutate, adding a new entity or removing an existing one, and the
chapter states plainly that "if you aren't careful when you add and remove
objects from the list you're iterating, you can end up with subtle bugs"
(Nystrom, "Update Method," verified 2026-08-23). this entry's own dimension
11 covers the two named bug shapes directly.

## 8. Implementation variants

Unity's own MonoBehaviour component model is the most directly documented
production variant. every MonoBehaviour subclass may override an
`Update()` method, and Unity's own engine calls it once per frame on every
active, enabled component in the scene, the identical shape Nystrom's
chapter describes, confirmed via Unity's own MonoBehaviour lifecycle
documentation (verified 2026-08-23). Microsoft's own XNA framework names
the same shape at two levels, a `Game.Update()` override on the top-level
game class and a separate `GameComponent.Update()` on each attached
component, so the pattern appears both at the whole-game level and at the
per-object level within one framework (Microsoft, XNA Game and
GameComponent classes, verified 2026-08-23).

Nystrom's own text names a further concrete example directly, the open
source Quintus JavaScript game engine's own `Sprite` class, which "has an
`update()` method that the engine calls on the sprite once per frame"
(Nystrom, "Update Method," verified 2026-08-23), the same identical shape a
third time in a third language and engine.

This entry attempted to independently verify Godot Engine's own
`queue_free()` deferred-removal mechanism as a fourth variant, since it is
a commonly cited answer to the mutating-collection hazard from dimension 7,
queuing a node for removal at the end of the current frame rather than
removing it mid-iteration. the fetch of Godot's own documentation page
returned content that was truncated before the specific `queue_free()`
mechanics could be confirmed verbatim, so this entry reports the pattern's
existence as plausible but not independently confirmed from Godot's own
source in this pass, an honest gap rather than a claim dressed up as
sourced.

## 9. Known production uses

Akka's own actor model documentation is this entry's strongest verified
non-game match, confirming a real, current, non-game production system
built on the identical per-tick, one-object-processes-its-own-turn shape.
"an actor is a container for state, behavior, a mailbox, child actors and a
supervisor strategy," where "an actor processes one message at a time"
(Akka, "Actor Systems," verified 2026-08-23), the same self-contained,
uniformly-invoked-per-turn behaviour the update method pattern describes,
even though Akka's own trigger is a message arriving rather than a fixed
frame tick.

Two further systems are real but only partial, architecturally adjacent
matches, and this entry reports that distinction directly rather than
overstating the fit. SimPy, a Python discrete-event simulation framework,
drives independent process generators forward on each simulated event
rather than a fixed per-frame `update()` call, a genuinely different
triggering model even though the independent-object shape is similar. GSAP,
a JavaScript animation library, runs its own internal ticker that advances
every active tween once per animation frame, which is closer to the
pattern's own cadence but is scoped specifically to animation state rather
than a general per-object update. neither is presented as a confirmed
direct implementation of the pattern, both are reported as adjacent,
verified systems worth knowing rather than exact matches.

## 10. Consequences

The pattern's own direct benefit is the one stated in dimension 2, each
object's own per-frame behaviour stays local to that object's own class,
so adding a new kind of object never touches the loop itself, only adds a
new `update()` override. the loop stays uniform and simple regardless of
how many distinct object kinds exist, which is the same benefit the
chapter's own motivating skeleton-patrol example is built to demonstrate
by contrast against the mushed-together alternative.

The cost is the mutating-collection hazard from dimension 7, which the
pattern does not resolve on its own, and a second, subtler cost this
entry did not find directly quantified in the sourced material. calling
`update()` uniformly on every object every frame, even ones that are
dormant, off-screen, or waiting, spends CPU time on objects doing nothing
useful that frame, a cost this entry reports as a reasoned extension of
the pattern's own uniform-call structure rather than a sourced claim, since
the chapter's own text does not discuss the performance cost of an
expensive `update()` call directly.

## 11. Failure modes and misuse

Nystrom's own text names two distinct, concrete bug shapes under its own
Keep in Mind heading. the first, the skip bug, happens when an object
removes itself from the collection mid-iteration using an index-based
removal that shifts every later element down by one, so "the next object
in the list gets skipped" because the loop's own index now points past it
(Nystrom, "Update Method," verified 2026-08-23). the chapter's own stated
mitigation is to walk the collection backwards when removal is index-based,
so a removal only shifts already-visited elements, never an unvisited one.

The second, the new-object-during-iteration bug, happens when one object's
own `update()` call adds a brand new object to the same collection being
iterated, and depending on the collection's own iteration mechanics, that
new object either gets its own `update()` called in the very same frame it
was created, or the iteration itself becomes invalid entirely (Nystrom,
"Update Method," verified 2026-08-23). the chapter's own stated mitigation
is to cache the object count at the start of the frame's iteration, so
newly added objects are simply skipped until the next frame rather than
processed, added, or corrupting the loop mid-pass.

## 12. Trade-off matrix

| Dimension | Update method, per-object dispatch | One central branch on object kind |
|---|---|---|
| Adding a new object kind | Add one new class, no loop change, dimension 2 | Edit the central branch every time |
| Loop simplicity | Stays uniform regardless of object variety, dimension 5 | Grows more tangled per new kind |
| Mid-iteration mutation | A real, sourced hazard, dimension 7 and 11 | Not applicable, no shared iteration |
| Per-frame cost | Every object charged every frame, dimension 10 | Only active branches ever run |
| Best fit | Many independent, similarly-shaped objects, dimension 4 | A small, fixed, rarely-changing set |
| Cross-cutting change | Change one method, applies everywhere it is called | Search and edit every branch |

## 13. Related and incompatible patterns

Nystrom's own chapter names its closest relations twice over, once inline
across the running text and once in a dedicated See Also section, and this
entry transcribes both directly rather than summarising loosely. Game Loop
is named inline three separate times as the pattern's own outer driver, the
"once per frame" cadence from dimension 1 that calls every object's
`update()`, and this catalogue's own Game Loop entry is the pattern this
entry cites for that cadence throughout. Component is named inline as the
natural next step once an object's own `update()` grows large enough to
split across separate concerns, each concern becoming its own component
with its own smaller `update()`. Type Object and State are each named
inline too, Type Object for sharing per-kind data across many object
instances that each still need their own `update()` call, and State for
structuring one object's own `update()` logic when its behaviour changes
across distinct phases.

The chapter's own dedicated See Also section names the pattern's role
directly, calling Game Loop, Component, and Update Method together its own
"trinity" of patterns that most game engines rest on, Game Loop driving the
cadence, Update Method giving each object its own turn within that cadence,
and Component letting one object's own turn be split across independent
pieces (Nystrom, "Update Method," verified 2026-08-23). the same section
also names Data Locality directly, since a collection of objects being
walked and updated every frame is exactly the access pattern Data Locality
optimises the memory layout for, and it names Unity's own MonoBehaviour,
Microsoft's own XNA `Game` and `GameComponent` classes, and the Quintus
`Sprite` class as real, concrete implementations, all three already covered
in this entry's own dimension 8.

This entry explicitly checked whether Update Method's own See Also section
names Object Pool or Dirty Flag and confirmed neither is present, matching
what this catalogue's own Object Pool and Dirty Flag entries each report
from their own side, that no sourced bridge back to Update Method exists in
either direction. Update Method has no directly incompatible pattern named
in the sourced material.

## 14. Refactoring path in and out

Refactoring a central, branch-on-object-kind loop into the update method
pattern starts from the chapter's own motivating example, per dimension 2,
by defining one shared base type with a single `update()` method, then
moving each branch's own logic into its own subclass override, one kind at
a time, verifying after each move that the loop itself still only calls the
one shared method and never branches on kind again. once every kind has its
own override, decide the mutating-collection handling from dimension 7 up
front, walking backwards for index-based removal and caching the frame's
own object count before adding new objects, rather than discovering either
bug shape from dimension 11 in production.

Refactoring out of the pattern, back toward a more centralised dispatch, is
driven by the cost from dimension 10 becoming a real, measured problem, a
very large collection of mostly-dormant objects each still paying for a
call every frame with nothing to do, at which point separating active from
inactive objects into distinct collections, only walking the active one,
addresses the cost directly without abandoning the per-object `update()`
shape itself.

## 15. Testing and verification

This entry explicitly checked the primary source for a stated testing
methodology and did not find one, the chapter's own text does not discuss
how to test or verify an update-method implementation, and this entry
reports that absence directly rather than inventing a technique dressed up
as sourced. in its absence, the two named bug shapes from dimension 11 give
a direct, reasoned starting point for a test suite. assert that removing an
object during a backwards iteration never skips the object immediately
before it, per the skip bug's own stated mechanism, and assert that an
object added during the current frame's iteration is not itself updated
until the following frame, per the cached-object-count mitigation's own
stated behaviour, both derived directly from the chapter's own quoted
mitigations rather than from any independently sourced test methodology.

## 16. Observability signals

Frame time spent inside the per-object update walk, measured as its own
distinct segment of the frame budget this catalogue's own Game Loop entry
establishes, is the most direct signal for the dormant-object cost from
dimension 10, a rising share of frame time attributable to `update()` calls
whose objects took no meaningful action is the leading indicator that
separating active from inactive objects, per dimension 14's own refactor
path, is due.

Collection size and mutation count per frame, objects added and objects
removed during a single frame's own iteration, are the direct signals for
the mutating-collection hazard from dimension 7 and dimension 11. a spike
in either, correlated with a rendering glitch or a missed behaviour report,
is the concrete symptom of the skip bug or the new-object-during-iteration
bug actually occurring in a running system, not merely a theoretical risk.

## 17. Security and privacy implications

This entry did not find the sourced material addressing a security or
privacy concern for the update method pattern directly, and reports that
absence rather than inventing one. the one plausible, reasoned extension of
the pattern's own structure, not a citation from the sourced material, is
that a per-object `update()` call given unrestricted access to the shared
collection it is itself being iterated within can, if untrusted or
third-party object code is ever mixed into that same collection, both read
and mutate state belonging to unrelated objects mid-iteration, a concern
that only matters when object code is not fully trusted, which the primary
book source's own game-engine context does not consider.

## 18. References

1. Nystrom, Robert, "Update Method," Game Programming Patterns,
   https://gameprogrammingpatterns.com/update-method.html, verified
   2026-08-23.
2. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
3. Akka, "Actor Systems," Akka documentation, verified 2026-08-23.
4. Unity Technologies, "MonoBehaviour," Unity Scripting Reference, verified
   2026-08-23.
5. Microsoft, "Game Class" and "GameComponent Class," XNA Framework
   documentation, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the update method pattern,
an `update()` call driven uniformly per object by a collection walk, with
both mitigations from dimension 11 applied directly. removal walks the
collection backwards so a removal only shifts already-visited entries, and
a newly added entity is not updated until the following frame because the
walk caches the object count at the start of the pass.

```typescript
interface Entity {
  update(deltaTime: number): void;
  isDead(): boolean;
}

class World {
  private entities: Entity[] = [];
  private pendingAdds: Entity[] = [];

  add(entity: Entity): void {
    this.pendingAdds.push(entity);
  }

  update(deltaTime: number): void {
    const frameCount = this.entities.length;

    for (let i = frameCount - 1; i >= 0; i--) {
      const entity = this.entities[i];
      entity.update(deltaTime);
      if (entity.isDead()) {
        this.entities.splice(i, 1);
      }
    }

    for (const added of this.pendingAdds) {
      this.entities.push(added);
    }
    this.pendingAdds = [];
  }

  count(): number {
    return this.entities.length;
  }
}
```

```python
from abc import ABC, abstractmethod
from typing import List


class Entity(ABC):
    @abstractmethod
    def update(self, delta_time: float) -> None:
        ...

    @abstractmethod
    def is_dead(self) -> bool:
        ...


class World:
    def __init__(self) -> None:
        self._entities: List[Entity] = []
        self._pending_adds: List[Entity] = []

    def add(self, entity: Entity) -> None:
        self._pending_adds.append(entity)

    def update(self, delta_time: float) -> None:
        frame_count = len(self._entities)

        for i in range(frame_count - 1, -1, -1):
            entity = self._entities[i]
            entity.update(delta_time)
            if entity.is_dead():
                del self._entities[i]

        self._entities.extend(self._pending_adds)
        self._pending_adds = []

    def count(self) -> int:
        return len(self._entities)
```

```go
package updatemethod

type Entity interface {
	Update(deltaTime float64)
	IsDead() bool
}

type World struct {
	entities    []Entity
	pendingAdds []Entity
}

func (w *World) Add(entity Entity) {
	w.pendingAdds = append(w.pendingAdds, entity)
}

func (w *World) Update(deltaTime float64) {
	frameCount := len(w.entities)

	for i := frameCount - 1; i >= 0; i-- {
		entity := w.entities[i]
		entity.Update(deltaTime)
		if entity.IsDead() {
			w.entities = append(w.entities[:i], w.entities[i+1:]...)
		}
	}

	w.entities = append(w.entities, w.pendingAdds...)
	w.pendingAdds = nil
}

func (w *World) Count() int {
	return len(w.entities)
}
```
