# Chapter 15: Spatial and Geometric Data Structures

## 15.1 The Spatial Query Problem

Every structure so far has assumed a total order. You can ask a BST for everything between 40 and 60 because "between" means something on a line. In two or more dimensions it stops meaning anything: there is no ordering of points in the plane that keeps neighbors adjacent, so a sorted array of coordinates cannot answer "which restaurants are within 500 metres of me."

Spatial structures exist to answer three query types that ordered structures cannot:

- **Range query**: which objects fall inside this rectangle or circle?
- **Nearest neighbor (NN)**: which object is closest to this point? Which *k* are closest?
- **Intersection query**: which objects overlap this one?

The shared strategy is the same one trees always use — recursively partition the space so that a query can discard most of it without examining its contents. What differs is *how* the partition is chosen: by alternating coordinate (KD-tree), by fixed geometric subdivision (quadtree), or by grouping the objects themselves (R-tree).

## 15.2 K-Dimensional Trees (KD-Trees)

KD-trees partition k-dimensional space:

```
2D KD-Tree:
Level 0: Split on x-axis
Level 1: Split on y-axis
Level 2: Split on x-axis
...

        Split on x: x < 7
               │
         ┌─────┴─────┐
         │           │
    [2,3] │       [8,1]
          │
    Split on y: y < 5
         │
    ┌────┴────┐
    │         │
[1,8]     [5,4]
```

A KD-tree is a BST where the comparison dimension cycles with depth. At depth *d* in a k-dimensional tree, nodes compare on axis `d mod k`. Every node therefore splits space with an axis-aligned hyperplane, and the subtree below it occupies a rectangular cell.

**Construction.** Building a balanced KD-tree means choosing the median along the current axis at each level:

```python
def build_kdtree(points, depth=0):
    if not points:
        return None
    axis = depth % len(points[0])
    points.sort(key=lambda p: p[axis])       # O(n log n) per level
    mid = len(points) // 2
    return KDNode(
        point=points[mid],
        axis=axis,
        left=build_kdtree(points[:mid], depth + 1),
        right=build_kdtree(points[mid + 1:], depth + 1),
    )
```

Sorting at every level costs O(n log² n). Using a linear-time median selection (introselect / nth_element) brings it to O(n log n), which is what production implementations do.

**Nearest neighbor search** is where the structure earns its keep. Descend to the leaf containing the query point, then unwind — but at each ancestor, check whether the *splitting plane* is closer than the best distance found so far. If it is, the other side of that plane could hold something better and must be searched. If it isn't, an entire subtree is discarded.

```python
def nearest(node, target, best=None):
    if node is None:
        return best
    if best is None or dist(target, node.point) < dist(target, best):
        best = node.point

    axis = node.axis
    diff = target[axis] - node.point[axis]
    near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)

    best = nearest(near, target, best)
    # Only cross the splitting plane if a closer point could exist beyond it
    if abs(diff) < dist(target, best):
        best = nearest(far, target, best)
    return best
```

That pruning test — `abs(diff) < dist(target, best)` — is the entire algorithm. Everything else is bookkeeping.

**The curse of dimensionality.** KD-tree NN search is O(log n) on average in low dimensions and O(n) in the worst case. The worst case stops being rare as *k* grows: in high dimensions almost every cell is close enough to the query that the pruning test fails, and the search degenerates to a full scan. The rule of thumb is that KD-trees stop paying for themselves somewhere around k ≈ 10–20, or more precisely once n < 2^k. Beyond that, use approximate methods — LSH, or HNSW graphs, which is what modern vector databases do.

| Operation | Average | Worst case |
|-----------|---------|------------|
| Build | O(n log n) | O(n log n) |
| Insert | O(log n) | O(n) |
| Delete | O(log n) | O(n) |
| Nearest neighbor | O(log n) | O(n) |
| Range query | O(n^(1−1/k) + m) | O(n) |

KD-trees do not rebalance on insertion. A long-lived tree under heavy insertion degrades, and the standard fix is periodic bulk rebuild rather than rotations — rotating would break the axis-cycling invariant.

## 15.3 Quad Trees

Divide 2D space into four quadrants recursively:

```
Level 0:        ┌─────────┐
               │         │
               │         │
               └─────────┘
Level 1:    ┌───┬───┐
           │ NW │ NE │
           ├───┼───┤
           │ SW │ SE │
           └───┴───┘
```

Where a KD-tree splits on a data point, a quadtree splits on *geometry* — always at the exact centre of the current cell, regardless of what the data looks like. That single difference drives everything else about the structure.

**Point quadtrees** subdivide a cell once it holds more than some threshold of points. **Region quadtrees** subdivide until each cell is uniform — the classic use is image compression, where a solid-colored region collapses to a single leaf no matter how large it is.

```python
class QuadTree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary      # (x, y, width, height)
        self.capacity = capacity
        self.points = []
        self.divided = False

    def insert(self, point):
        if not self.boundary.contains(point):
            return False
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True
        if not self.divided:
            self.subdivide()          # create nw, ne, sw, se
        return (self.nw.insert(point) or self.ne.insert(point)
                or self.sw.insert(point) or self.se.insert(point))
```

Because the subdivision is geometric rather than data-driven, depth depends on how clustered the data is, not on how much of it there is. A million points spread evenly gives a shallow tree; a thousand points stacked nearly on top of each other gives a very deep one. Implementations guard this with a maximum depth.

The 3D generalization is the **octree** (eight children instead of four), used throughout graphics for frustum culling, collision broadphase, and voxel storage — Minecraft-style voxel worlds are octrees.

## 15.4 R-Trees

R-trees index rectangles/hyper-rectangles:

```
R-Tree:
        ┌──────────────────┐
        │   [MBR of all]    │
        │  ┌──┐      ┌──┐   │
        │  │  │      │  │   │
        │  └──┘      └──┘   │
        │    ┌──────┐      │
        │    │      │      │
        │    └──────┘      │
        └──────────────────┘
```

KD-trees and quadtrees index *points*. R-trees index *extended objects* — roads, building footprints, delivery zones — and they are the structure databases actually ship.

An R-tree is a B-tree whose keys are **minimum bounding rectangles (MBRs)**. Each internal entry stores the MBR enclosing everything in its subtree. A query descends into every child whose MBR intersects the query region — which may be more than one, and that is the crucial difference from a B-tree. Where a B-tree descends exactly one path, an R-tree may descend several.

This gives R-trees B-tree virtues: balanced by construction, high fanout, tuned to disk pages, and O(log n) height. It also gives them their central problem: **overlap**. Sibling MBRs may intersect, and every intersection means a query that could have followed one path now follows two. Search degrades toward O(n) as overlap grows.

The whole R-tree literature is about controlling overlap when a node splits and its entries must be divided in two. Guttman's original 1984 paper offered linear and quadratic split heuristics. The **R*-tree** (Beckmann et al., 1990) minimizes a combination of overlap, MBR area, and margin, and reinserts a fraction of entries on overflow instead of splitting immediately; it is meaningfully better in practice and is what most implementations mean by "R-tree" today. The **R+-tree** eliminates overlap entirely by duplicating objects across cells, trading space and update cost for query speed.

For static data, **bulk loading** by sorting along a space-filling curve (Sort-Tile-Recursive packing) produces far better trees than repeated insertion.

## 15.5 Grids, Geohashes, and Space-Filling Curves

The simplest spatial index is a **uniform grid**: divide space into fixed cells, hash each object into the cells it touches. Insert and point lookup are O(1), which no tree can match. The catch is that a grid has no way to adapt — cell size must be chosen up front, and real geographic data is wildly non-uniform. A grid sized for Manhattan is useless for Montana.

**Space-filling curves** offer a different trick: map 2D coordinates to a single number that mostly preserves locality, then use an ordinary B-tree.

- **Z-order (Morton) curve**: interleave the bits of x and y. Cheap to compute, but has discontinuities where the curve jumps across the space.
- **Hilbert curve**: better locality preservation and no long jumps, at higher computational cost.

**Geohash** applies Z-order to latitude/longitude and base-32 encodes the result, so that a shared string prefix means geographic proximity — `u4pruyd` and `u4pruyf` are neighbors. This makes spatial proximity queryable in any plain key-value store, which is why geohashes are everywhere. The failure mode is boundary effects: two points either side of a major cell boundary are physically adjacent but share no prefix, so correct implementations query the eight neighboring cells as well.

Production systems have largely moved to hierarchical cell systems built on this idea: Google's **S2** (Hilbert curve projected onto a sphere) and Uber's **H3** (hexagonal cells, so all neighbors are equidistant — which matters for routing and surge pricing).

## 15.6 Choosing a Spatial Structure

| Structure | Best for | Weakness |
|-----------|----------|----------|
| Uniform grid | Uniform density, fast updates | Non-uniform data wastes space or overflows cells |
| KD-tree | Static point sets, low dimensions, kNN | Degrades badly above ~10 dimensions; no rebalancing |
| Quadtree / Octree | Clustered 2D/3D points, image regions, collision broadphase | Depth driven by clustering, not data size |
| R-tree / R*-tree | Extended objects, disk-resident data, GIS | Overlap degrades queries; complex splits |
| Geohash / S2 / H3 | Distributed stores, sharding by location | Boundary effects need neighbor queries |
| HNSW / LSH | High-dimensional similarity search | Approximate, not exact |

The practical decision tree is short. Points or shapes? Shapes means R-tree. Points in memory and static? KD-tree. Points, clustered, and 2D/3D? Quadtree or octree. Needs to live in a database or shard across machines? Geohash or S2. More than ~20 dimensions? Give up on exactness and use HNSW.

## 15.7 Applications

**KD-Trees:**
- Nearest neighbor search
- Point clouds
- Ray tracing

**Quad Trees:**
- Image compression
- Collision detection
- Sparse data

**R-Trees:**
- Geographic Information Systems
- Database spatial indexes
- Map applications

In shipped systems: PostGIS and Oracle Spatial index with R-trees (PostgreSQL's GiST is a generalized R-tree); SQLite ships an R*-tree module; MongoDB and Redis use geohash-backed indexes for `$near` and `GEORADIUS`; scikit-learn's `KDTree` and `BallTree` back its neighbor queries; game engines use octrees and BSP trees for visibility and collision; and ray tracers use KD-trees or bounding volume hierarchies — a BVH is essentially an R-tree for triangles.

## 15.8 Historical Context

Jon Bentley introduced KD-trees in 1975 while a graduate student at Stanford, as a multidimensional generalization of binary search. Raphael Finkel and Bentley described quadtrees the previous year, in 1974. Antonin Guttman published the R-tree in 1984 specifically to make spatial data indexable on disk, and the R*-tree refinement followed from Beckmann, Kriegel, Schneider, and Seeger in 1990.

The space-filling curves are much older than the structures that use them: Giuseppe Peano constructed the first in 1890 and David Hilbert described his variant in 1891, as pure mathematics with no application in view. G. M. Morton put Z-order to work for geographic databases at IBM in 1966 — a rare case of a piece of nineteenth-century mathematics arriving in computing essentially unchanged.
