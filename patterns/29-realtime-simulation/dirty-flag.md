---
name: Dirty Flag
slug: dirty-flag
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Dirty Bit, Lazy Recomputation, Cache Invalidation Flag]
first_described: "Robert Nystrom's Dirty Flag chapter in Game Programming Patterns, in the book's own Optimization Patterns part"
maturity: canonical
related: [game-loop]
incompatible_with: []
verified: 2026-08-23
---

# Dirty Flag

## 1. Name, aliases, and lineage

A dirty flag marks a piece of derived, cached data as out of sync with the
primary data it was computed from, so the expensive recomputation only
happens lazily, when the derived value is actually needed, rather than
eagerly on every change to the primary data.

The clearest, directly verified source is Robert Nystrom's own chapter,
which this entry fetched directly (Nystrom, Robert, "Dirty Flag," Game
Programming Patterns, https://gameprogrammingpatterns.com/dirty-flag.html,
verified 2026-08-23), placed in the book's own Optimization Patterns part
alongside Object Pool, Data Locality, and Spatial Partition, confirmed via
the book's own table of contents (verified 2026-08-23, same source used
across this catalogue's other Nystrom-sourced entries in this family).

## 2. Problem and context

Recomputing a derived value eagerly, every time the primary data it depends
on changes, wastes work when the derived value is read far less often than
the primary data changes. Nystrom's own chapter introduces the problem with
a hierarchical scene-graph example, a pirate ship carrying a crow's nest, a
pirate, and a parrot, each with a local transform relative to its parent
and needing a derived world transform for rendering, where the naive,
eager approach recomputes the parrot's own world position four separate
times in a single frame even though only the final result before rendering
was ever actually needed (Nystrom, "Dirty Flag," verified 2026-08-23). this
problem shows up anywhere a piece of cached, derived state changes upstream
far more often than it is read downstream.

## 3. Forces

Nystrom's own text names the central tension as a choice between two
computation timings, each with a real cost. eager, immediate recalculation
avoids any staleness but spends CPU whether or not the result is ever
actually read, while deferred, lazy recalculation on read can save that
wasted work but risks a noticeable pause at the moment the value is
finally needed, if a large amount of accumulated change must all be
resolved at once (Nystrom, "Dirty Flag," verified 2026-08-23). the source
explicitly likens this exact trade to a well-known one in language
runtimes, reference counting against a stop-the-world garbage collector,
immediate small costs paid continuously versus deferred larger costs paid
occasionally.

Nystrom's own text also states the pattern's own precondition directly,
against reaching for it by default. the primary data must change more
often than the derived data is actually read, and the derived computation
should be hard to update incrementally, since keeping a running total
instead of recomputing from scratch is preferable whenever that is
practical (Nystrom, "Dirty Flag," verified 2026-08-23), with an explicit
caution that "like most optimizations, you should only reach for it when
you have a performance problem big enough to justify the added code
complexity" (Nystrom, "Dirty Flag," verified 2026-08-23).

## 4. Applicability and non-applicability

The pattern applies whenever a genuine change-to-read ratio favours
deferring the computation, per dimension 3's own stated precondition, and
it is not limited to games. browser layout engines apply the identical
idea under the identical name. "in order not to do a full layout for every
small change, browsers use a dirty bit system. a renderer that is changed
or added marks itself and its children as dirty, needing layout" (Tali
Garsiel and Paul Irish, "How Browsers Work," web.dev,
https://web.dev/howbrowserswork, verified 2026-08-23), a direct, real,
non-game production use of the same eager-versus-lazy trade-off from
dimension 3.

Microsoft's own Excel support documentation confirms the concept applies to
spreadsheet recalculation too, without using the pattern's own vocabulary.
"to avoid unnecessary calculations that can waste your time and slow down
your computer, Microsoft Excel automatically recalculates formulas only
when the cells that the formula depends on have changed" (Microsoft,
"Description of Excel recalculation and iterative calculation,"
https://support.microsoft.com/en-us/office/description-of-excel-recalculation-and-iterative-calculation-73fc7dac-91cf-4d36-86e8-67124f6bcce4,
verified 2026-08-23), a real, verified confirmation of the same lazy-
recomputation idea, described in plain, user-facing language rather than
the pattern's own internal terminology.

The pattern is a poor fit, per dimension 3's own stated precondition, when
derived data is read as often as, or more often than, the primary data
changes, since the deferred computation then buys nothing and merely adds
the bookkeeping cost of tracking the flag itself.

## 5. Structure

Nystrom's own text states the pattern's full definition directly, in a
single quoted passage. "A set of primary data changes over time. A set of
derived data is determined from this using some expensive process. A
dirty flag tracks when the derived data is out of sync with the primary
data. It is set when the primary data changes. If the flag is set when the
derived data is needed, then it is reprocessed and the flag is cleared.
Otherwise, the previous cached derived data is used" (Nystrom, "Dirty
Flag," verified 2026-08-23).

The chapter's own worked implementation, per dimension 2's scene-graph
example, holds a cached world transform plus a boolean dirty flag on each
node. a setTransform call updates the local state and sets the flag, and a
render call checks the flag before recomputing, using the cached value when
clean. Nystrom's own text describes a further technique for the
hierarchical case specifically, passing a dirty parameter down the
hierarchy during traversal, so a parent's own dirtiness propagates to force
recomputation of its children's world transforms without every child
separately tracking whether an ancestor changed (Nystrom, "Dirty Flag,"
verified 2026-08-23).

## 6. ASCII structure diagram

```
  primary data changes
  (e.g. setTransform on a node)
       |
       v
  dirty flag SET
  (parent's dirtiness propagates
   down to its children too)
       |
       .
       .   time passes, primary data
       .   may change again, flag stays SET
       |
       v
  derived data is READ
  (e.g. render() needs the world transform)
       |
  +----+----+
  |         |
flag SET   flag CLEAR
  |         |
  v         v
recompute   use the cached
the derived  derived value
value, then  as-is, no work
CLEAR the    done
flag
```

## 7. Dynamics

Nystrom's own Design Decisions section names three real timing choices for
when the flag is actually cleaned. when the value is next needed, avoiding
unnecessary work but risking a pause, at checkpoints such as a loading
screen or cutscene, hidden from the person, or in the background on a
timer, which requires concurrency support (Nystrom, "Dirty Flag," verified
2026-08-23). the same section names a granularity choice, fine-grained
tracking of exactly what changed, more memory overhead for the bookkeeping,
against coarse-grained tracking, less bookkeeping but reprocessing
unchanged data alongside changed data.

Browser layout engines implement a real, two-flag version of the
hierarchical propagation from dimension 5 directly. "there are two flags,
dirty, and children are dirty which means that although the renderer itself
may be OK, it has at least one child that needs a layout" (Garsiel and
Irish, "How Browsers Work," verified 2026-08-23), letting the engine skip
walking into a subtree whose own root is clean even when checking whether
recomputation is needed anywhere below it.

## 8. Implementation variants

Nystrom's own See Also section names a real, non-game production
implementation directly. "this pattern is common outside of games in
browser-side web frameworks like Angular. They use dirty flags to track
which data has been changed in the browser and needs to be pushed up to
the server" (Nystrom, "Dirty Flag," verified 2026-08-23). the same section
names a second real domain, physics engines. "physics engines track which
objects are in motion and which are resting. Since a resting body won't
move until an impulse is applied to it, they don't need processing until
they get touched. This is-moving bit is a dirty flag to note which objects
have had forces applied and need to have their physics resolved" (Nystrom,
"Dirty Flag," verified 2026-08-23), the inverse framing of the same idea, a
flag marking when work IS needed rather than when a cache is stale.

Browser layout engines, per dimension 7's two-flag citation, and
Microsoft Excel's own dependency-driven recalculation, per dimension 4,
are two further real, independently verified non-game implementations of
the identical lazy-recomputation idea, described in each source's own
domain-specific vocabulary rather than the pattern's own terminology.

## 9. Known production uses

Angular, per dimension 8's direct citation from the primary source itself,
is a real, widely used browser framework applying dirty flags to track
which data changed and needs to be pushed to the server. Browser layout
engines broadly, per dimension 7's citation, apply the same idea to avoid
recomputing layout for a whole page on every small DOM change, a real,
current, universal production use running in every browser rendering the
web.

Microsoft Excel, per dimension 4's citation, is a real, current, massively
deployed production application applying the identical lazy, dependency-
driven recalculation idea to spreadsheet formulas, described in its own
support documentation in user-facing rather than internal-architecture
language.

## 10. Consequences

The pattern eliminates wasted recomputation directly, per dimension 2's
own worked example, the parrot's world transform recomputed four times in
a frame collapses to at most once, whenever it is actually read. this
consequence scales with the change-to-read ratio from dimension 3. the
more often primary data changes relative to how rarely derived data is
read, the larger the saved work.

The trade, per dimension 3, is a real risk of a visible pause at the
moment the derived value is finally needed, if a large amount of deferred
work has accumulated, and the added code complexity of tracking the flag
correctly, both to set it, per dimension 11's own primary failure mode,
and, in a hierarchical structure, to propagate it, per dimension 5's
downward-propagation technique.

## 11. Failure modes and misuse

Forgetting to SET the dirty flag on some mutation path is the more
dangerous, more directly sourced failure mode, and it is addressed by the
primary source itself, at length. "You have to make sure to set the flag
every time the state changes... Miss it in one place, and your program
will incorrectly use stale derived data. This leads to confused players
and bugs that are very hard to track down" (Nystrom, "Dirty Flag," verified
2026-08-23), a passage the source itself connects to Phil Karlton's
well-known aphorism about cache invalidation being one of the two hard
problems in computer science. the source's own stated mitigation is
structural. "encapsulating modifications to the primary data behind some
interface. If anything that can change the state goes through a single
narrow API, you can set the dirty flag there and rest assured that it
won't be missed" (Nystrom, "Dirty Flag," verified 2026-08-23).

Forgetting to CLEAR the flag after recomputing, the opposite mistake,
causing every subsequent read to redundantly recompute forever, is a
failure mode this entry explicitly checked for in the primary source and
confirmed is not discussed there at all, and no second, citable source for
this specific sub-bug was found within the available research. this is
reported as an honest, open gap rather than an invented failure mode. it
is functionally a correctness-preserving but performance-destroying bug,
the opposite risk profile from the forget-to-set case, which corrupts
correctness silently.

## 12. Trade-off matrix

| Dimension | Dirty flag, lazy recomputation | Eager, immediate recomputation |
|---|---|---|
| CPU spent when data changes but is never read | None, per dimension 2 | Wasted, spent regardless |
| Worst-case read latency | A pause is possible, dimension 3 | Always fast, already current |
| Code complexity | Higher, must set and often propagate the flag correctly | Lower, no flag to track |
| Correctness risk | Real, per dimension 11's forget-to-set bug | Not applicable, always current |
| Best fit | Change-heavy, read-rarely data, dimension 3 | Read-as-often-as-changed data |
| Real non-game precedent | Angular and physics engines (dimension 8), browser layout (dimension 7), Excel (dimension 4) | The naive default everywhere else |

## 13. Related and incompatible patterns

Nystrom's own See Also section names two real-world domains rather than
other chapters in the book, per dimension 8's own citations, Angular and
physics engines, not a cross-reference to a sibling pattern. this entry
explicitly checked Update Method's own See Also section for a reference
back to Dirty Flag and confirmed one is not present there either, the same
absence found for this catalogue's own Object Pool entry. so, like Object
Pool, Dirty Flag has no sourced connection to the Game Loop and Update
Method per-frame cadence that bridges this catalogue's own Game Loop,
Entity-Component-System, and Spatial Partitioning entries, and this entry
reports that absence directly.

Dirty Flag shares a structural family resemblance with this catalogue's
own Object Pool and Spatial Partitioning entries, all three sit in
Nystrom's own Optimization Patterns part of the book, per dimension 1, but
this entry found no direct, sourced cross-reference between Dirty Flag and
either of them.

Dirty Flag has no directly incompatible pattern named in the sourced
material. the three timing choices and the two granularity choices from
dimension 7 are alternative implementations of the same idea rather than
incompatible designs.

## 14. Refactoring path in and out

Refactoring eager recomputation into a dirty flag starts by measuring the
actual change-to-read ratio, per dimension 3's own stated precondition,
since the pattern helps only when primary data changes more often than
derived data is read. add the boolean flag, set it on every mutation path,
and, per dimension 11's own stated mitigation, route those mutations
through a single narrow interface so the flag can never be missed. move
the recomputation itself behind a read-time check, clearing the flag once
recomputed, and, for a hierarchical structure, add the downward-
propagation technique from dimension 5 so a parent's dirtiness reaches its
children without every node separately tracking ancestor state.

Refactoring out of a dirty flag, back to eager recomputation or an
incrementally-updated running value, is driven by discovering the actual
change-to-read ratio never justified the pattern, per dimension 4's non-
applicability case, or by the read-time pause from dimension 3 becoming a
real, measured problem in its own right, in which case moving the
recomputation to a background timer, per dimension 7's third timing
option, is the more targeted fix rather than abandoning the pattern
entirely.

## 15. Testing and verification

This entry explicitly checked the primary source and could not find a
citable technique for testing a dirty-flag mechanism, comparing a cached
value against a freshly recomputed reference value, and no substitute
source was located within the available research. this is an honest,
reported negative result, not an invented methodology.

In its absence, the reasoned, generally applicable approach follows
directly from what the pattern is meant to preserve, per dimension 5's own
definition. the cached derived value, whenever the flag reads clean, must
always equal what a fresh, from-scratch recomputation would produce. a
test can assert this directly. mutate the primary data through every
mutation path the system exposes, read the derived value, and compare it
against an independently, eagerly recomputed reference. this test catches
both failure modes from dimension 11 at once. a missed set call surfaces
as a mismatch between the cached and the reference value, and, separately,
asserting the flag is false immediately after a read catches a missed
clear call.

## 16. Observability signals

Read-time recomputation duration, measured directly at the moment the flag
is found set, is the most direct signal for the pause risk from dimension
3. a duration that grows without bound signals the accumulated-change
problem the eager-versus-lazy trade-off exists to trade against, and is
the practical evidence for whether a background-timer cleaning strategy,
per dimension 7, is worth adopting.

The flag's own set-to-clear ratio, how often it is set relative to how
often it is actually cleared by a read, names the change-to-read ratio
dimension 3 and dimension 4 depend on directly, measured rather than
assumed. a ratio far from the assumption the pattern was adopted under is
direct evidence to revisit the refactor-out decision from dimension 14.

A cache-mismatch check, comparing the cached value against a freshly
recomputed reference on a sampled subset of reads rather than every read,
is a lightweight, production-safe variant of the testing technique from
dimension 15, catching the forget-to-set failure mode from dimension 11 in
production rather than only in tests.

## 17. Security and privacy implications

The forget-to-set failure mode from dimension 11 has a real security
reading when the cached derived value is security-relevant rather than
purely visual, such as a cached permission or access-control decision
derived from primary state. Nystrom's own quoted mitigation from dimension
11, encapsulating every mutation path behind a single narrow interface so
the flag can never be missed, is a genuinely stronger requirement in this
case than in the purely cosmetic scene-graph example the source itself
uses, since a stale, more-permissive cached decision served after a
permission was actually revoked is a real access-control failure, not
merely a visual glitch. this entry did not find either primary or
secondary source discussing this security-specific framing directly, and
reports it as this entry's own reasoned extension of dimension 11's own
correctness concern, applied to a security-sensitive derived value rather
than a cosmetic one.

Angular's own real, cited use from dimension 8, tracking which data
changed and needs to be pushed to the server, means a missed dirty flag on
the client side could also mean a change a person made is silently never
synced to the server at all, a data-loss risk distinct from, but adjacent
to, the stale-read risk named above.

## 18. References

1. Nystrom, Robert, "Dirty Flag," Game Programming Patterns,
   https://gameprogrammingpatterns.com/dirty-flag.html, verified
   2026-08-23.
2. Garsiel, Tali, and Paul Irish, "How Browsers Work," web.dev,
   https://web.dev/howbrowserswork, verified 2026-08-23.
3. Microsoft, "Description of Excel recalculation and iterative
   calculation,"
   https://support.microsoft.com/en-us/office/description-of-excel-recalculation-and-iterative-calculation-73fc7dac-91cf-4d36-86e8-67124f6bcce4,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of a hierarchical dirty-flag
transform node, following the pirate-ship scene-graph shape from dimension
2, with the downward-propagation technique from dimension 5.

```typescript
interface Vec3 {
  x: number;
  y: number;
  z: number;
}

function composeWorld(local: Vec3, parentWorld: Vec3): Vec3 {
  return { x: local.x + parentWorld.x, y: local.y + parentWorld.y, z: local.z + parentWorld.z };
}

class TransformNode {
  private local: Vec3 = { x: 0, y: 0, z: 0 };
  private cachedWorld: Vec3 = { x: 0, y: 0, z: 0 };
  private dirty = true;
  private children: TransformNode[] = [];

  addChild(child: TransformNode): void {
    this.children.push(child);
  }

  setLocalTransform(value: Vec3): void {
    this.local = value;
    this.dirty = true;
  }

  getWorldTransform(parentWorld: Vec3, parentDirty: boolean): Vec3 {
    if (this.dirty || parentDirty) {
      this.cachedWorld = composeWorld(this.local, parentWorld);
      this.dirty = false;
      for (const child of this.children) {
        child.getWorldTransform(this.cachedWorld, true);
      }
    }
    return this.cachedWorld;
  }
}
```

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


def compose_world(local: Vec3, parent_world: Vec3) -> Vec3:
    return Vec3(local.x + parent_world.x, local.y + parent_world.y, local.z + parent_world.z)


class TransformNode:
    def __init__(self) -> None:
        self._local = Vec3()
        self._cached_world = Vec3()
        self._dirty = True
        self._children: List["TransformNode"] = []

    def add_child(self, child: "TransformNode") -> None:
        self._children.append(child)

    def set_local_transform(self, value: Vec3) -> None:
        self._local = value
        self._dirty = True

    def get_world_transform(self, parent_world: Vec3, parent_dirty: bool) -> Vec3:
        if self._dirty or parent_dirty:
            self._cached_world = compose_world(self._local, parent_world)
            self._dirty = False
            for child in self._children:
                child.get_world_transform(self._cached_world, True)
        return self._cached_world
```

```go
package dirtyflag

type Vec3 struct {
	X, Y, Z float64
}

func composeWorld(local, parentWorld Vec3) Vec3 {
	return Vec3{X: local.X + parentWorld.X, Y: local.Y + parentWorld.Y, Z: local.Z + parentWorld.Z}
}

type TransformNode struct {
	local        Vec3
	cachedWorld  Vec3
	dirty        bool
	children     []*TransformNode
}

func NewTransformNode() *TransformNode {
	return &TransformNode{dirty: true}
}

func (n *TransformNode) AddChild(child *TransformNode) {
	n.children = append(n.children, child)
}

func (n *TransformNode) SetLocalTransform(value Vec3) {
	n.local = value
	n.dirty = true
}

func (n *TransformNode) GetWorldTransform(parentWorld Vec3, parentDirty bool) Vec3 {
	if n.dirty || parentDirty {
		n.cachedWorld = composeWorld(n.local, parentWorld)
		n.dirty = false
		for _, child := range n.children {
			child.GetWorldTransform(n.cachedWorld, true)
		}
	}
	return n.cachedWorld
}
```
