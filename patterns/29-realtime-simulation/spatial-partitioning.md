---
name: Spatial Partitioning
slug: spatial-partitioning
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Spatial Partition, Spatial Index, Broad-Phase Collision Structure]
first_described: "Robert Nystrom's Spatial Partition chapter in Game Programming Patterns names the family of structures directly; the individual structures it covers, grids, quadtrees, BSP trees, k-d trees, and bounding volume hierarchies, each have their own separate, much older lineage in computational geometry, so this entry reports the pattern-catalogue framing and the underlying structures' ages as two distinct claims rather than one origin"
maturity: canonical
related: [game-loop]
incompatible_with: []
verified: 2026-08-23
---

# Spatial Partitioning

## 1. Name, aliases, and lineage

Spatial partitioning divides space into a data structure so that a spatial
query, which objects are near this point, which pairs might be colliding,
which objects fall inside this view, runs against a small, nearby subset of
objects rather than every object in the world.

The clearest, directly verified pattern-catalogue source is Robert
Nystrom's own chapter, which frames the family of structures without
picking one as canonical. "I've tried not to discuss specific spatial
partitioning structures in detail here to keep the chapter high-level... but
your next step from here should be to learn a few of the common structures"
(Nystrom, Robert, "Spatial Partition," Game Programming Patterns,
https://gameprogrammingpatterns.com/spatial-partition.html, verified
2026-08-23). Nystrom's own text names five common structures and, notably,
maps each to a familiar one-dimensional data structure it generalizes. "A
grid is a persistent bucket sort. BSPs, k-d trees, and bounding volume
hierarchies are binary search trees. Quadtrees and octrees are tries"
(Nystrom, "Spatial Partition," verified 2026-08-23).

The individual structures Nystrom's chapter names each carry their own,
separate, older lineage in computational geometry rather than a single
shared origin. binary space partitioning traces to 1969 in the context of
3D computer graphics, extended in 1980 by Fuchs and colleagues to represent
3D scenes for real-time rendering (Wikipedia contributors, "Binary space
partitioning," https://en.wikipedia.org/wiki/Binary_space_partitioning,
verified 2026-08-23). this entry reports the pattern-catalogue framing and
each structure's own age as two distinct, separately sourced claims rather
than collapsing them into one origin story.

## 2. Problem and context

Checking every object in a simulation against every other object for
proximity or collision costs O(n squared) tests, since "the number of
pairwise tests we have to perform each frame increases with the square of
the number of units" (Nystrom, "Spatial Partition," verified 2026-08-23).
Wikipedia's own Collision detection article states the same problem in
formal terms. "for n objects, n(n-1)/2 intersection tests are needed with a
naive approach. This quadratic growth makes such an approach computationally
expensive as n increases" (Wikipedia contributors, "Collision detection,"
https://en.wikipedia.org/wiki/Collision_detection, verified 2026-08-23).
this problem shows up in any simulation, game, physics engine, or spatial
database, that must repeatedly answer proximity, range, or intersection
queries over a large or growing number of objects.

## 3. Forces

Nystrom's own text names the central trade twice, once for the general
technique and once for its cost. "Spatial partitions exist to knock an O(n)
or O(n squared) operation down to something more manageable," and "a
spatial partition also uses additional memory for its bookkeeping data
structures. Like many optimizations, it trades memory for speed" (Nystrom,
"Spatial Partition," verified 2026-08-23).

A second, sharper tension is objects that move. Nystrom's own text states
it directly. "objects that change position are harder to deal with. You'll
have to reorganize the data structure... and that adds code complexity and
spends CPU cycles" (Nystrom, "Spatial Partition," verified 2026-08-23). a
structure well suited to static, unmoving geometry can be a poor fit for a
scene full of constantly moving objects, since every move is a potential
rebuild or reinsert.

A third tension, the choice between a uniform grid and a hierarchical tree,
depends entirely on how the objects are distributed in space, elaborated
fully in dimensions 5 and 11. neither structure is universally better, and
the wrong choice for a given distribution actively hurts performance rather
than merely failing to help.

## 4. Applicability and non-applicability

Spatial partitioning applies whenever the number of objects and the
frequency of proximity queries makes the O(n squared) naive approach from
dimension 2 genuinely expensive, collision detection in a game or physics
engine, nearest-neighbor and range queries in a spatial database, or view
frustum culling in a renderer. the applicability is not limited to games.
PostGIS, a real, current, production spatial database extension, states its
own rationale in the same terms. "Without indexing, a search for features
requires a sequential scan of every record in the database. Indexing speeds
up searching by organizing the data into a structure which can be quickly
traversed to find matching records" (PostGIS, "Spatial Indexes,"
https://postgis.net/docs/using_postgis_dbmanagement.html, verified
2026-08-23), using an R-tree structure from the same family Nystrom's
chapter names. MongoDB's own geospatial indexing documentation confirms a
second, independent non-game production use for the identical underlying
problem (MongoDB, "Geospatial Queries,"
https://www.mongodb.com/docs/manual/geospatial-queries/, verified
2026-08-23).

The pattern is unnecessary, or actively costly, when the object count is
small enough that the naive O(n squared) check is cheap in absolute terms.
Nystrom's own stated memory cost from dimension 3 means a spatial partition
spends real memory and maintenance work that a small scene simply does not
need to recover.

## 5. Structure

Nystrom's own chapter names five common structures, each mapped to a
familiar one-dimensional analogue, per dimension 1's quote. a grid, a
persistent bucket sort. quadtrees and octrees, tries. BSP trees, k-d trees,
and bounding volume hierarchies, binary search trees (Nystrom, "Spatial
Partition," verified 2026-08-23).

A quadtree recursively subdivides 2D space, where "each internal node has
exactly four children," most often "to partition a two-dimensional space by
recursively subdividing it into four quadrants" (Wikipedia contributors,
"Quadtree," https://en.wikipedia.org/wiki/Quadtree, verified 2026-08-23).
its 3D analogue, the octree, subdivides space into eight octants per level
in the same recursive way (Wikipedia contributors, "Octree,"
https://en.wikipedia.org/wiki/Octree, verified 2026-08-23), and Nystrom's
own chapter independently names the octree as the quadtree's 3D analogue
directly (Nystrom, "Spatial Partition," verified 2026-08-23).

A bounding volume hierarchy wraps groups of objects in progressively larger
bounding volumes arranged as a tree, so that "as a ray traverses through the
tree, any time it does not intersect a node's bounds, the subtree beneath
that node can be skipped" (pbrt, "Bounding Volume Hierarchies,"
https://pbr-book.org/4ed/Primitives_and_Intersection_Acceleration/Bounding_Volume_Hierarchies,
verified 2026-08-23), and, unlike a grid or a quadtree that subdivides
space itself, "each primitive appears in the hierarchy only once" (pbrt,
"Bounding Volume Hierarchies," verified 2026-08-23), since a BVH subdivides
the object SET rather than the space those objects occupy.

## 6. ASCII structure diagram

```
  world space, before partitioning:

  +----------------------------------+
  |  o     o          o              |
  |     o        o          o    o   |
  |  o       o                       |
  |            o    o     o          |
  +----------------------------------+
     N objects, N(N-1)/2 naive pair checks

  divided into a quadtree, only nearby cells checked:

  +----------------+----------------+
  |  o     o       |        o       |
  |     o          |    o       o   |
  +----------------+----------------+
  |  o       o     |  o    o     o  |
  |                |                |
  +----------------+----------------+
       ^
       query point, checks only its own cell
       and immediate neighbors, not the whole world
```

## 7. Dynamics

A spatial partition is queried in two phases in practice. a broad phase
that uses the structure to cheaply eliminate most pairs, followed by a
narrow phase that runs the expensive, exact test only on the small
remaining candidate set. Wikipedia's own Collision detection article states
the measured result of this two-phase approach directly. "the number of
required narrow phase collision tests was O(n+m) where n is the number of
objects and m is the number of objects at close proximity. This is a
significant improvement over the quadratic complexity of the naive
approach" (Wikipedia contributors, "Collision detection," verified
2026-08-23). the same source frames the mechanism plainly. "If one splits
space into a number of simple cells, and if two objects can be shown not to
be in the same cell, then they need not be checked for intersection"
(Wikipedia contributors, "Collision detection," verified 2026-08-23).

For a scene with moving objects, per dimension 3's cited cost, the
structure must be kept current every simulation step. Nystrom's own text
notes that hierarchical, adaptive structures are "more frequently used for
art and static geometry that stays fixed during the game" (Nystrom,
"Spatial Partition," verified 2026-08-23), implicitly because a structure
that must reorganize itself on every object move pays that reorganization
cost every single step, which is the harder, dynamic-geometry case this
entry's dimension 11 covers as a real, sourced failure mode.

## 8. Implementation variants

Binary space partitioning has a real, historically significant production
implementation in id Software's Doom and Quake, independently confirmed
through Wikipedia's own BSP article rather than a secondary blog summary.
"This algorithm, together with the description of BSP trees in the
standard computer graphics textbook of the day... was used by John Carmack
in the making of Doom," and "this was used in Quake and contributed
significantly to that game's performance" (Wikipedia contributors, "Binary
space partitioning," verified 2026-08-23). The same source names the
structure's own construction cost directly. "generating a BSP tree can be
time-consuming. Typically, it is therefore performed once on static
geometry, as a pre-calculation step" (Wikipedia contributors, "Binary space
partitioning," verified 2026-08-23), which is the same static-versus-moving
tension named generally in dimension 3 and dimension 7, now attributed to a
specific, real structure and a specific, real game engine.

A bounding volume hierarchy has a real, current production implementation
in Box2D, a widely used open-source physics engine, which states directly
that it uses "a bounding volume hierarchy (dynamic tree)... for game
specific spatial sorting needs" (Box2D, "Documentation,"
https://box2d.org/documentation/, verified 2026-08-23). pbrt's own text
names multiple real BVH construction algorithms trading build cost against
tree quality, from a fast, simple midpoint split to the slower, better
Surface Area Heuristic (pbrt, "Bounding Volume Hierarchies," verified
2026-08-23), and states a direct, sourced trade-off against a competing
structure. "BVHs are more efficient to build than kd-trees, and are
generally more numerically [reliable]... than kd-trees are" (pbrt, "Bounding
Volume Hierarchies," verified 2026-08-23).

## 9. Known production uses

Doom and Quake, per dimension 8's independently confirmed citation, are
real, historically significant, shipped commercial games built on BSP
trees for both rendering and collision. Box2D, a real, current, widely used
open-source physics engine, ships a bounding volume hierarchy as its
broad-phase collision structure, per dimension 8.

Outside games entirely, PostGIS and MongoDB are real, current, production
spatial databases that apply the identical two-phase broad-phase-then-exact
strategy from dimension 7 to a completely different domain. PostGIS's own
documentation names the specific structure it uses. "PostGIS uses an
R-Tree index implemented on top of GiST to index spatial data. GiST is the
most commonly-used and versatile spatial index method" (PostGIS, "Spatial
Indexes," verified 2026-08-23), and states the same two-phase pattern by
name. "Spatial indexes store only the bounding box of geometries. Spatial
queries use the index as a primary filter" before "a spatial predicate
function" runs the exact, narrow-phase test (PostGIS, "Spatial Indexes,"
verified 2026-08-23). MongoDB's own 2dsphere index documentation confirms a
second, independent production database use of the same family of
structures for spherical proximity and containment queries (MongoDB,
"Geospatial Queries," verified 2026-08-23).

pbrt, the physically based renderer whose own book is cited across
dimensions 5 and 8, is itself a real, production-grade rendering system
using a bounding volume hierarchy as its primary ray-intersection
acceleration structure, not merely a textbook description of one (pbrt,
"Bounding Volume Hierarchies," verified 2026-08-23).

## 10. Consequences

The pattern turns an O(n squared) all-pairs check into an O(n plus m) broad
phase, per dimension 7's cited result, which is the entire reason the
pattern exists. this consequence scales, a scene with ten times as many
objects sees a far smaller than hundredfold increase in query cost, which
is what makes the memory and maintenance cost Nystrom names in dimension 3
worth paying at real scale.

The trade, per dimension 3, is memory spent on the structure's own
bookkeeping and, for a scene with moving objects, per dimension 7, ongoing
maintenance cost every simulation step to keep the structure current. a
structure chosen for the wrong object distribution, per dimension 5's
grid-versus-hierarchy framing, can consume that memory and maintenance cost
without delivering a real query-time improvement, which is the specific
failure mode dimension 11 covers in detail.

## 11. Failure modes and misuse

A uniform grid sized wrong for the actual object distribution is the most
direct, sourced failure mode. Nystrom's own text names both directions of
the mistake. cells too large mean "if objects clump together, you get worse
performance there while wasting memory in the empty areas," and cells too
small mean "that outer loop can start to matter," the overhead of iterating
many near-empty cells (Nystrom, "Spatial Partition," verified 2026-08-23).
this is the concrete shape of the density-mismatch failure. a grid tuned
for one distribution of objects actively hurts performance under a
different, clumpier distribution rather than merely failing to help.

A hierarchical structure has the opposite failure mode under the same
condition. "since hierarchical space partitions don't subdivide sparse
regions, a large empty space will remain a single partition," so "if you
have a bunch of objects all clumped together, a non-hierarchical partition
can be ineffective" while a quadtree, which "only recursively subdivide[s]
squares that have a high population... adapts to the set of objects"
(Nystrom, "Spatial Partition," verified 2026-08-23). so the grid-versus-tree
choice from dimension 3 is not a matter of taste. a grid suits a roughly
uniform distribution, a tree suits a clustered one, and choosing the wrong
one for the actual data is a real, sourced misuse.

A quadtree specifically has a second, structural failure mode independent
of density. Wikipedia's own article names it directly. "inserting in a bad
order can lead to a tree of height linear in the number of input points (at
which point it becomes a linked-list)" (Wikipedia contributors, "Quadtree,"
verified 2026-08-23), degenerating the tree's expected logarithmic query
cost into linear cost under an adversarial or simply unlucky insertion
order.

## 12. Trade-off matrix

| Dimension | Uniform grid | Hierarchical tree (quadtree, octree, BVH) |
|---|---|---|
| Uniform object density | Strong fit, dimension 11 | Wastes subdivisions on empty cells, dimension 11 |
| Clustered or non-uniform density | Wastes memory in empty cells, dimension 11 | Adapts to population, dimension 11 |
| Construction cost | Cheap, a bucket sort per dimension 1 | Higher, especially SAH-quality BVH build, dimension 8 |
| Moving objects | Simple to update, cell reassignment | Costly to update, per dimension 3 and 7 |
| Insertion-order sensitivity | Not applicable | Real for a quadtree, degenerates under bad order, dimension 11 |
| Best-known real use | Broad-phase collision in simple scenes | Doom/Quake BSP, Box2D and pbrt BVH, dimension 8 |

## 13. Related and incompatible patterns

Spatial Partitioning is related to this catalogue's own Game Loop entry as
a reasoned, practical pairing rather than a documented one. this entry
explicitly checked Nystrom's own Spatial Partition chapter's "See Also"
section for a cross-reference to Game Loop and confirmed one is not
present, and separately checked Nystrom's own Game Loop chapter's own "See
Also" section for a reference back, finding only Fiedler's article, a game-
loops overview article, and Unity's documentation named there (Nystrom,
"Game Loop," verified 2026-08-23). the practical pairing, rebuild or update
the structure once per simulation step, then query it, per dimension 7's
own dynamics, is a real, common engineering practice this entry reports as
inferred rather than sourced.

Spatial Partitioning is similarly related to this catalogue's own Entity-
Component-System entry as an inferred, not documented, pairing. a system
that needs proximity or collision information commonly queries a spatial
partition rather than scanning every entity, per dimension 4's
applicability case, and this entry reports that connection the same way,
plainly labeled as its own reasoning rather than a citation from either
primary source.

Spatial Partitioning has no directly incompatible pattern named in the
sourced material. its own internal choice between a grid and a
hierarchical tree, per dimension 3 and the trade-off matrix in dimension
12, is a choice between implementations of the same idea rather than
incompatible patterns.

## 14. Refactoring path in and out

Refactoring a naive all-pairs check into spatial partitioning starts by
measuring the actual object distribution, roughly uniform or clustered, per
dimension 11's grid-versus-tree finding, since that distribution determines
which structure to build, not personal preference. build the chosen
structure once, wire the broad-phase query in ahead of the existing exact
pairwise test rather than replacing that test, per dimension 7's two-phase
dynamics, so the narrow phase stays correct while the broad phase only
narrows the candidate set it runs against. only after the broad phase is
verified to return the same candidate set the naive check would have
examined, using the brute-force comparison technique from dimension 15,
should the naive all-pairs loop be removed entirely.

Refactoring out of spatial partitioning, back to a naive check, is driven
by discovering the object count and query frequency never justified the
memory and maintenance cost from dimension 3 in the first place, per
dimension 4's non-applicability case, or by the structure being rebuilt
every step for a highly dynamic scene, per dimension 7, at a cost that
approaches or exceeds what the naive check would have cost directly.

## 15. Testing and verification

This entry directly checked both Nystrom's own Spatial Partition chapter
and Wikipedia's own Collision detection article for a documented testing or
validation technique, and confirmed neither discusses one. this is an
honest, reported negative result, not an invented methodology, and a
sourced, standard testing technique for this specific pattern remains an
open gap in this entry's research.

In its absence, the reasoned, generally applicable approach follows
directly from what the structure is meant to preserve. because the broad
phase from dimension 7 exists only to narrow the candidate set the narrow
phase examines, not to change the final answer, a spatial partition can be
tested by comparing its query results against the naive O(n squared)
brute-force check on the same object set, and asserting the two produce
identical candidate pairs, differing only in how many pairs the exact test
had to examine. this test catches an incorrect structure directly, since
any query that returns a different candidate set than the brute-force
reference is provably wrong, and it composes naturally with the density
scenarios from dimension 11, run the comparison test under both a uniform
and a clustered object distribution to catch the grid-versus-tree failure
mode specifically.

## 16. Observability signals

Average candidate-set size per query, measured directly, is the most
direct signal for whether the structure fits the actual object
distribution. a candidate set that stays small and roughly constant as the
total object count grows confirms the O(n plus m) result from dimension 7
is genuinely being delivered. a candidate set that grows with total object
count, rather than local density, signals the density mismatch from
dimension 11, cells or nodes too large for how clustered the objects
actually are.

Structure rebuild or reinsert cost per simulation step, measured directly
rather than assumed, names the dynamic-scene cost from dimension 3 and
dimension 7. a rebuild cost that approaches the cost the naive check would
have taken without any structure at all is the direct signal that the
structure is no longer paying for itself, per dimension 14's refactor-out
condition.

For a hierarchical tree specifically, tree depth relative to the expected
logarithmic bound, sampled periodically, names the degenerate-insertion
failure mode from dimension 11 before it silently turns every query
linear.

## 17. Security and privacy implications

Outside games, per dimension 9's PostGIS and MongoDB citations, the objects
a spatial partition indexes are frequently real people's real locations,
which makes the pattern's own primary purpose, answering proximity queries
fast, a genuine privacy surface rather than a purely performance concern.
a spatial index that makes "who is near this point" cheap to compute is
exactly the capability that makes a location-tracking or de-anonymization
query cheap to run at scale, and this entry did not find either primary
source, or PostGIS's or MongoDB's own documentation as fetched in this
research pass, discussing that trade-off directly. this is reported as a
genuine, reasoned extension of general location-data handling practice, not
a citation from the sourced material, and it argues for the same
access-control and query-auditing discipline any system handling real
location data needs, applied at the query layer in front of the spatial
index rather than assumed to be handled by the index itself.

Within a game, the availability concern from this catalogue's own Game Loop
entry applies here too. an attacker able to influence how many objects a
spatial partition must track or rebuild each step, per dimension 3's
maintenance cost, can drive the same kind of resource-exhaustion pressure
that entry's dimension 17 describes for an unbounded simulation catch-up
loop.

## 18. References

1. Nystrom, Robert, "Spatial Partition," Game Programming Patterns,
   https://gameprogrammingpatterns.com/spatial-partition.html, verified
   2026-08-23.
2. Wikipedia contributors, "Binary space partitioning,"
   https://en.wikipedia.org/wiki/Binary_space_partitioning, verified
   2026-08-23.
3. Wikipedia contributors, "Collision detection,"
   https://en.wikipedia.org/wiki/Collision_detection, verified 2026-08-23.
4. PostGIS, "Spatial Indexes,"
   https://postgis.net/docs/using_postgis_dbmanagement.html, verified
   2026-08-23.
5. MongoDB, "Geospatial Queries,"
   https://www.mongodb.com/docs/manual/geospatial-queries/, verified
   2026-08-23.
6. Wikipedia contributors, "Quadtree,"
   https://en.wikipedia.org/wiki/Quadtree, verified 2026-08-23.
7. Wikipedia contributors, "Octree," https://en.wikipedia.org/wiki/Octree,
   verified 2026-08-23.
8. pbrt, "Bounding Volume Hierarchies,"
   https://pbr-book.org/4ed/Primitives_and_Intersection_Acceleration/Bounding_Volume_Hierarchies,
   verified 2026-08-23.
9. Box2D, "Documentation," https://box2d.org/documentation/, verified
   2026-08-23.

## Code

TypeScript, Python, and Go implementations of a uniform-grid spatial
partition, the simplest structure Nystrom names in dimension 5, storing
each object under the cell its position falls into and querying only the
objects in a point's own cell and its eight neighbors.

```typescript
interface Point {
  x: number;
  y: number;
}

class SpatialGrid<T extends { position: Point }> {
  private cells = new Map<string, T[]>();

  constructor(private cellSize: number) {}

  private key(x: number, y: number): string {
    const cx = Math.floor(x / this.cellSize);
    const cy = Math.floor(y / this.cellSize);
    return cx + "," + cy;
  }

  insert(item: T): void {
    const key = this.key(item.position.x, item.position.y);
    const bucket = this.cells.get(key);
    if (bucket) {
      bucket.push(item);
    } else {
      this.cells.set(key, [item]);
    }
  }

  clear(): void {
    this.cells.clear();
  }

  queryNear(point: Point): T[] {
    const cx = Math.floor(point.x / this.cellSize);
    const cy = Math.floor(point.y / this.cellSize);
    const results: T[] = [];
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const bucket = this.cells.get((cx + dx) + "," + (cy + dy));
        if (bucket) results.push(...bucket);
      }
    }
    return results;
  }
}
```

```python
import math
from dataclasses import dataclass
from typing import Dict, Generic, List, Tuple, TypeVar


@dataclass
class Point:
    x: float
    y: float


T = TypeVar("T")


class SpatialGrid(Generic[T]):
    def __init__(self, cell_size: float) -> None:
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[T]] = {}

    def _key(self, x: float, y: float) -> Tuple[int, int]:
        return (math.floor(x / self.cell_size), math.floor(y / self.cell_size))

    def insert(self, item: T, position: Point) -> None:
        key = self._key(position.x, position.y)
        self.cells.setdefault(key, []).append(item)

    def clear(self) -> None:
        self.cells.clear()

    def query_near(self, point: Point) -> List[T]:
        cx, cy = self._key(point.x, point.y)
        results: List[T] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                bucket = self.cells.get((cx + dx, cy + dy))
                if bucket:
                    results.extend(bucket)
        return results
```

```go
package spatialgrid

import "math"

type Point struct {
	X, Y float64
}

type cellKey struct {
	CX, CY int
}

type SpatialGrid[T any] struct {
	cellSize float64
	cells    map[cellKey][]T
}

func New[T any](cellSize float64) *SpatialGrid[T] {
	return &SpatialGrid[T]{
		cellSize: cellSize,
		cells:    make(map[cellKey][]T),
	}
}

func (g *SpatialGrid[T]) key(x, y float64) cellKey {
	return cellKey{
		CX: int(math.Floor(x / g.cellSize)),
		CY: int(math.Floor(y / g.cellSize)),
	}
}

func (g *SpatialGrid[T]) Insert(item T, position Point) {
	key := g.key(position.X, position.Y)
	g.cells[key] = append(g.cells[key], item)
}

func (g *SpatialGrid[T]) Clear() {
	g.cells = make(map[cellKey][]T)
}

func (g *SpatialGrid[T]) QueryNear(point Point) []T {
	center := g.key(point.X, point.Y)
	results := make([]T, 0)
	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			k := cellKey{CX: center.CX + dx, CY: center.CY + dy}
			if bucket, ok := g.cells[k]; ok {
				results = append(results, bucket...)
			}
		}
	}
	return results
}
```
