---
name: Data Locality
slug: data-locality
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Cache-Friendly Layout, Contiguous Component Storage]
first_described: "Robert Nystrom's Data Locality chapter in Game Programming Patterns, in the book's own Optimization Patterns part"
maturity: canonical
related: [object-pool, entity-component-system]
incompatible_with: []
verified: 2026-08-23
---

# Data Locality

## 1. Name, aliases, and lineage

Data locality arranges the data a hot loop touches contiguously in memory,
so the CPU's own automatic cache-line prefetch keeps paying off across the
whole pass, instead of chasing scattered pointers.

This entry names it "Data Locality" to match the real-time-simulation
primary source directly, distinct from the general, stack-agnostic sense
the term also carries elsewhere in software engineering. the clearest,
directly verified source here is Robert Nystrom's own chapter, fetched
directly (Nystrom, Robert, "Data Locality," Game Programming Patterns,
https://gameprogrammingpatterns.com/data-locality.html, verified
2026-08-23). the chapter's own stated intent, quoted directly. "Accelerate
memory access by arranging data to take advantage of CPU caching" (Nystrom,
"Data Locality," verified 2026-08-23). Nystrom's own book places the
chapter in its Optimization Patterns part, alongside this catalogue's own
Object Pool and Spatial Partitioning entries, confirmed via the book's own
table of contents (https://gameprogrammingpatterns.com/contents.html,
verified 2026-08-23).

## 2. Problem and context

The chapter opens not with a code example but with a cache-cost argument,
quoted directly. "with today's hardware, it can take hundreds of cycles to
fetch a byte of data from RAM," and "whenever your chip needs a byte of
data from RAM, it automatically grabs a whole chunk of contiguous memory,
usually around 64 to 128 bytes, and puts it in the cache" (Nystrom, "Data
Locality," verified 2026-08-23). the author's own measured demonstration
follows directly. "I wrote two programs that did the exact same
computation. The only difference was how many cache misses they caused.
The slow one was fifty times slower than the other" (Nystrom, "Data
Locality," verified 2026-08-23).

The concrete, code-level version of the problem appears later, in the
chapter's own Sample Code section, as a game loop walking entities each
holding separate pointers off to their own AI, physics, and render
components scattered elsewhere in the heap. "the scary part is that we
have no idea how these objects are laid out in memory. We're completely
at the mercy of the memory manager" (Nystrom, "Data Locality," verified
2026-08-23). a second, distinct example, a particle system, appears still
later in the chapter's own "Packed data" subsection.

## 3. Forces

The chapter's own text names the direct trade. "in order to please this
pattern, you will have to sacrifice some of your precious abstractions...
you will have to give up inheritance, interfaces, and the benefits those
tools can provide. There's no silver bullet here, only challenging
trade-offs" (Nystrom, "Data Locality," verified 2026-08-23), set against
the cache-line payoff from dimension 2. "whenever the chip reads some
memory, it gets a whole cache line. The more you can use stuff in that
cache line, the faster you go" (Nystrom, "Data Locality," verified
2026-08-23).

## 4. Applicability and non-applicability

The chapter's own two-part When to Use It guidance is direct and narrow.
"like most optimizations, the first guideline for using the Data Locality
pattern is when you have a performance problem," and, specific to this
pattern, "you'll also want to be sure your performance problems are caused
by cache misses. If your code is slow for other reasons, this won't help"
(Nystrom, "Data Locality," verified 2026-08-23).

The chapter's own text warns against over-applying the pattern's own
techniques too. sorting a packed array to keep active elements contiguous
should not itself run every frame. "I'm not saying you should quicksort
the entire collection of particles every frame. That would more than
eliminate the gains here" (Nystrom, "Data Locality," verified 2026-08-23),
and hot and cold field splitting is framed as skippable when performance
is not genuinely critical.

## 5. Structure

The chapter's own core statement of the mechanism, quoted directly.
"organize your data structures so that the things you're processing are
next to each other in memory" (Nystrom, "Data Locality," verified
2026-08-23). the chapter's own worked fix replaces per-entity pointers
with three separate, contiguous component arrays, one each for AI,
physics, and render data, each processed by "a straight crawl through
three contiguous arrays" (Nystrom, "Data Locality," verified 2026-08-23)
instead of chasing pointers off a single per-entity array. a second
technique, hot and cold splitting, keeps only the frequently-touched
fields inline in the array element and moves rarely-touched fields, such
as loot-drop data, out to a separate structure reached by pointer only
when actually needed.

## 6. ASCII structure diagram

```
  poor locality, pointer-chasing layout:

  GameEntity[i] --> pointer --> AIComponent (scattered)
  GameEntity[i] --> pointer --> PhysicsComponent (scattered)
  GameEntity[i] --> pointer --> RenderComponent (scattered)

  each frame chases three pointers per entity, three
  separate cache misses, layout at the mercy of the
  memory manager.

  data-locality layout, contiguous component arrays:

  AIComponent[0] AIComponent[1] AIComponent[2] ...
  PhysicsComponent[0] PhysicsComponent[1] ...
  RenderComponent[0] RenderComponent[1] ...

  each system walks its own array start to end, a
  straight crawl, the cache-line prefetch keeps paying
  off across the whole pass.

  hot and cold split, within one component array:

  hot field (touched every frame)   inline, in the array
  cold field (touched rarely)       moved out, reached
                                     via a pointer only
                                     when actually needed
```

## 7. Dynamics

Each frame, per the chapter's own text, the relevant system walks its own
contiguous component array start to end, touching only the fields it
needs. the chapter also discusses maintaining the packed array's own
tight, contiguous invariant as objects are added and removed at runtime,
tied directly to this entry's own dimension 13 cross-reference to Object
Pool, and cautions against re-sorting that array every frame as a way of
ruining the very gains being pursued, per dimension 4.

## 8. Implementation variants

Unity's own Entities (DOTS) package documents a genuine, live-verified
production implementation of chunk-based contiguous component storage.
"all entities and components with the same archetype are stored in
uniform blocks of memory called chunks," and "each chunk consists of 16
KiB," with "an array for each component type, plus an additional array to
store the entity IDs," where "the arrays of a chunk are tightly packed,
the first entity of the chunk is stored at index 0 of these arrays, the
second entity at index 1" (Unity Technologies, "Archetypes concept," Unity
Entities package manual, verified 2026-08-23).

This entry explicitly checked Unity's own archetype and component concept
pages for an explicit CPU cache-line or memory-bandwidth justification for
this chunk layout and confirmed it is not stated on either fetched page,
reporting that absence directly rather than papering over it. Unity's own
docs confirm the what, tightly packed, structure-of-arrays-shaped chunk
storage, without the why. the causal cache-miss reasoning is the chapter's
own distinct contribution, and per this entry's own dimension 13, the
chapter itself credits Tony Albrecht's paper and Noel Llopis's blog post
as the primary sources for that reasoning, rather than claiming it as
original.

## 9. Known production uses

The chapter's own See Also section names one directly, quoted in full
under dimension 13. the Artemis game engine, "one of the first and
better-known frameworks that uses simple IDs for game entities" (Nystrom,
"Data Locality," verified 2026-08-23). this entry reports the book's own
citation as given, without independently re-confirming that specific link
still resolves in 2026.

## 10. Consequences

The chapter's own measured benefit, quoted directly. "this pumps a solid
stream of bytes right into the hungry maw of the CPU. In my testing, this
change made the update loop fifty times faster than the previous version"
(Nystrom, "Data Locality," verified 2026-08-23). the cost is the
abstraction sacrifice already quoted in dimension 3, giving up inheritance
and interfaces in exchange for the contiguous layout the pattern demands.

## 11. Failure modes and misuse

The chapter's own text warns against premature optimization directly, per
dimension 4, applying the pattern to code that is not genuinely a measured
cache-miss bottleneck. a second, distinct failure mode the chapter names
is branch misprediction from a naive active-flag check inside the hot
loop. "doing an if check for every particle can cause a branch
misprediction and a pipeline stall... when the loop is constantly toggling
between particles that are and aren't active, that prediction fails. When
it does, the CPU has to ditch the instructions it had started
speculatively processing, a pipeline flush, and start over" (Nystrom,
"Data Locality," verified 2026-08-23), motivating the chapter's own
sorted-active-particles technique rather than a per-element branch.

## 12. Trade-off matrix

| Dimension | Contiguous component arrays | Per-entity pointers to scattered components |
|---|---|---|
| Cache behaviour | One prefetch feeds a straight crawl, dimension 6 | A cache miss per pointer chased, dimension 2 |
| Measured cost | Fifty times faster in the author's own test, dimension 10 | The naive baseline the author measured against |
| Abstraction cost | Gives up inheritance and interfaces, dimension 3 | Full OOP flexibility retained |
| Branch behaviour | Sorted-active technique avoids mispredicts, dimension 11 | A naive if check risks pipeline stalls |
| Best fit | A measured, cache-miss-caused hot loop, dimension 4 | Code that is not a measured bottleneck |
| Add or remove at runtime | Needs a packing discipline, dimension 7 | Trivial, pointers can point anywhere |

## 13. Related and incompatible patterns

Nystrom's own See Also section, transcribed in full. "much of this
chapter revolves around the Component pattern, and that pattern is
definitely one of the most common data structures that gets optimized for
cache usage... using the Component pattern makes this optimization easier."
"Tony Albrecht's Pitfalls of Object-Oriented Programming is probably the
most widely-read introduction to designing your game's data structures
for cache-friendliness." "around the same time, Noel Llopis wrote a very
influential blog post on the same topic." "this pattern almost invariably
takes advantage of a contiguous array of homogenous objects. Over time,
you'll very likely be adding and removing objects from that array. The
Object Pool pattern is about exactly that." "the Artemis game engine is
one of the first and better-known frameworks that uses simple IDs for
game entities" (Nystrom, "Data Locality," verified 2026-08-23).

This entry explicitly checked whether the chapter names Update Method,
Spatial Partitioning, or Event Queue in that same See Also section. Update
Method is present only inline, in an aside inside the Sample Code section,
"as the name implies, these are examples of the Update Method pattern," not
inside the formal See Also list, a distinction this entry reports
precisely rather than presenting Update Method as a See Also citation.
Spatial Partitioning and Event Queue are both confirmed absent from the
See Also section entirely. Inline, not in See Also, the chapter also links
directly to Type Object, "one way to keep much of the flexibility of
polymorphism without using subclassing is through the Type Object
pattern."

## 14. Refactoring path in and out

The chapter's own gate for refactoring into the pattern is the applicability
test from dimension 4, a measured, cache-miss-caused performance problem,
never a default starting point. the chapter's own profiling guidance
names both a manual and a dedicated-tool path. "the cheap way to profile
is to manually add a bit of instrumentation that checks how much time has
elapsed between two points in the code," and, for cache-specific data, "an
excellent free option is Cachegrind. It runs your program on top of a
simulated CPU and cache hierarchy and then reports all of the cache
interactions" (Nystrom, "Data Locality," verified 2026-08-23). this entry
did not find guidance on migrating back out of a data-locality-optimized
layout, and reports that absence directly.

## 15. Testing and verification

This entry explicitly checked the full chapter for a discussed testing or
verification methodology and confirmed none exists, reporting that
absence directly rather than inventing one.

## 16. Observability signals

The chapter's own text names cache miss count and location directly as
the signal worth watching. "you really want to see how many cache misses
are occurring and where. Fortunately, there are profilers out there that
report this," naming Cachegrind by name as the free option, per dimension
14 (Nystrom, "Data Locality," verified 2026-08-23).

## 17. Security and privacy implications

This entry did not find the chapter addressing a security or privacy
concern, and did not find a reasoned extension of the pattern's own
structure worth offering here, since packing performance-critical struct
data contiguously does not present a security-relevant angle distinct
from generic memory-safety concerns that apply to any array-based buffer.

## 18. References

1. Nystrom, Robert, "Data Locality," Game Programming Patterns,
   https://gameprogrammingpatterns.com/data-locality.html, verified
   2026-08-23.
2. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
3. Unity Technologies, "Archetypes concept," Unity Entities package
   manual, verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of the contiguous component
array from dimension 5, an AI system walking one packed array instead of
chasing per-entity pointers.

```typescript
interface AiComponent {
  entityId: number;
  targetX: number;
  targetY: number;
}

class AiSystem {
  private components: AiComponent[] = [];

  add(component: AiComponent): void {
    this.components.push(component);
  }

  removeByEntityId(entityId: number): void {
    const index = this.components.findIndex((c) => c.entityId === entityId);
    if (index === -1) {
      return;
    }
    const last = this.components.length - 1;
    this.components[index] = this.components[last];
    this.components.pop();
  }

  update(): void {
    for (const component of this.components) {
      component.targetX += 1;
      component.targetY += 1;
    }
  }

  size(): number {
    return this.components.length;
  }
}
```

```python
from dataclasses import dataclass
from typing import List


@dataclass
class AiComponent:
    entity_id: int
    target_x: float
    target_y: float


class AiSystem:
    def __init__(self) -> None:
        self._components: List[AiComponent] = []

    def add(self, component: AiComponent) -> None:
        self._components.append(component)

    def remove_by_entity_id(self, entity_id: int) -> None:
        for i, component in enumerate(self._components):
            if component.entity_id == entity_id:
                self._components[i] = self._components[-1]
                self._components.pop()
                return

    def update(self) -> None:
        for component in self._components:
            component.target_x += 1
            component.target_y += 1

    def size(self) -> int:
        return len(self._components)
```

```go
package datalocality

type AiComponent struct {
	EntityID int
	TargetX  float64
	TargetY  float64
}

type AiSystem struct {
	components []AiComponent
}

func (s *AiSystem) Add(component AiComponent) {
	s.components = append(s.components, component)
}

func (s *AiSystem) RemoveByEntityID(entityID int) {
	for i, c := range s.components {
		if c.EntityID == entityID {
			last := len(s.components) - 1
			s.components[i] = s.components[last]
			s.components = s.components[:last]
			return
		}
	}
}

func (s *AiSystem) Update() {
	for i := range s.components {
		s.components[i].TargetX++
		s.components[i].TargetY++
	}
}

func (s *AiSystem) Size() int {
	return len(s.components)
}
```
