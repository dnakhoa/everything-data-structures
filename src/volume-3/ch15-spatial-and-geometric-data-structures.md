# Chapter 15: Spatial and Geometric Data Structures

## 15.1 The Spatial Query Problem

Every structure so far has assumed a total order. You can ask a BST for everything between 40 and 60 because "between" means something on a line. In two or more dimensions it stops meaning anything: there is no ordering of points in the plane that keeps neighbors adjacent, so a sorted array of coordinates cannot answer "which restaurants are within 500 metres of me."

Spatial structures exist to answer three query types that ordered structures cannot:

- **Range query**: which objects fall inside this rectangle or circle?
- **Nearest neighbor (NN)**: which object is closest to this point? Which *k* are closest?
- **Intersection query**: which objects overlap this one?

The shared strategy is the same one trees always use. Recursively partition the space so that a query can discard most of it without examining its contents. What differs is *how* the partition is chosen: by alternating coordinate (KD-tree), by fixed geometric subdivision (quadtree), or by grouping the objects themselves (R-tree).

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

**Nearest neighbor search** is where the structure earns its keep. Descend to the leaf containing the query point, then unwind, but at each ancestor, check whether the *splitting plane* is closer than the best distance found so far. If it is, the other side of that plane could hold something better and must be searched. If it isn't, an entire subtree is discarded.

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

That pruning test (`abs(diff) < dist(target, best)`)is the entire algorithm. Everything else is bookkeeping.

**The curse of dimensionality.** KD-tree NN search is O(log n) on average in low dimensions and O(n) in the worst case. The worst case stops being rare as *k* grows: in high dimensions almost every cell is close enough to the query that the pruning test fails, and the search degenerates to a full scan. The rule of thumb is that KD-trees stop paying for themselves somewhere around k ≈ 10–20, or more precisely once n < 2^k. Beyond that, use approximate methods. LSH, or HNSW graphs, which is what modern vector databases do.

| Operation | Average | Worst case |
|-----------|---------|------------|
| Build | O(n log n) | O(n log n) |
| Insert | O(log n) | O(n) |
| Delete | O(log n) | O(n) |
| Nearest neighbor | O(log n) | O(n) |
| Range query | O(n^(1−1/k) + m) | O(n) |

KD-trees do not rebalance on insertion. A long-lived tree under heavy insertion degrades, and the standard fix is periodic bulk rebuild rather than rotations. Rotating would break the axis-cycling invariant.

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

Where a KD-tree splits on a data point, a quadtree splits on *geometry*, always at the exact centre of the current cell, regardless of what the data looks like. That single difference drives everything else about the structure.

**Point quadtrees** subdivide a cell once it holds more than some threshold of points. **Region quadtrees** subdivide until each cell is uniform. The classic use is image compression, where a solid-colored region collapses to a single leaf no matter how large it is.

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

The 3D generalization is the **octree** (eight children instead of four), used throughout graphics for frustum culling, collision broadphase, and voxel storage, Minecraft-style voxel worlds are octrees.

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

KD-trees and quadtrees index *points*. R-trees index *extended objects* (roads, building footprints, delivery zones) and they are the structure databases actually ship.

An R-tree is a B-tree whose keys are **minimum bounding rectangles (MBRs)**. Each internal entry stores the MBR enclosing everything in its subtree. A query descends into every child whose MBR intersects the query region, which may be more than one, and that is the crucial difference from a B-tree. Where a B-tree descends exactly one path, an R-tree may descend several.

This gives R-trees B-tree virtues: balanced by construction, high fanout, tuned to disk pages, and O(log n) height. It also gives them their central problem: **overlap**. Sibling MBRs may intersect, and every intersection means a query that could have followed one path now follows two. Search degrades toward O(n) as overlap grows.

The whole R-tree literature is about controlling overlap when a node splits and its entries must be divided in two. Guttman's original 1984 paper offered linear and quadratic split heuristics. The **R*-tree** (Beckmann et al., 1990) minimizes a combination of overlap, MBR area, and margin, and reinserts a fraction of entries on overflow instead of splitting immediately; it is meaningfully better in practice and is what most implementations mean by "R-tree" today. The **R+-tree** eliminates overlap entirely by duplicating objects across cells, trading space and update cost for query speed.

For static data, **bulk loading**, either by sorting along a space-filling curve (Hilbert packing) or by Sort-Tile-Recursive (STR) packing, produces far better trees than repeated insertion.

## 15.5 Grids, Geohashes, and Space-Filling Curves

The simplest spatial index is a **uniform grid**: divide space into fixed cells, hash each object into the cells it touches. Insert and point lookup are O(1), which no tree can match. The catch is that a grid has no way to adapt. Cell size must be chosen up front, and real geographic data is wildly non-uniform. A grid sized for Manhattan is useless for Montana.

**Space-filling curves** offer a different trick: map 2D coordinates to a single number that mostly preserves locality, then use an ordinary B-tree.

- **Z-order (Morton) curve**: interleave the bits of x and y. Cheap to compute, but has discontinuities where the curve jumps across the space.
- **Hilbert curve**: better locality preservation and no long jumps, at higher computational cost.

**Geohash** applies Z-order to latitude/longitude and base-32 encodes the result, so that a shared string prefix means geographic proximity, `u4pruyd` and `u4pruyf` are neighbors. This makes spatial proximity queryable in any plain key-value store, which is why geohashes are everywhere. The failure mode is boundary effects: two points either side of a major cell boundary are physically adjacent but share no prefix, so correct implementations query the eight neighboring cells as well.

Production systems have largely moved to hierarchical cell systems built on this idea: Google's **S2** (Hilbert curve projected onto a sphere) and Uber's **H3** (hexagonal cells, so all neighbors are equidistant, which matters for routing and surge pricing).

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

In shipped systems: PostGIS and Oracle Spatial index with R-trees (PostgreSQL's GiST is a generalized R-tree); SQLite ships an R*-tree module; MongoDB and Redis use geohash-backed indexes for `$near` and `GEORADIUS`; scikit-learn's `KDTree` and `BallTree` back its neighbor queries; game engines use octrees and BSP trees for visibility and collision; and ray tracers use KD-trees or bounding volume hierarchies, a BVH is essentially an R-tree for triangles.

## 15.8 Historical Context

Jon Bentley introduced KD-trees in 1975 while a graduate student at Stanford, as a multidimensional generalization of binary search. Raphael Finkel and Bentley described quadtrees the previous year, in 1974. Antonin Guttman published the R-tree in 1984 specifically to make spatial data indexable on disk, and the R*-tree refinement followed from Beckmann, Kriegel, Schneider, and Seeger in 1990.

The space-filling curves are much older than the structures that use them: Giuseppe Peano constructed the first in 1890 and David Hilbert described his variant in 1891, as pure mathematics with no application in view. G. M. Morton put Z-order to work for geographic databases at IBM in 1966: a rare case of a piece of nineteenth-century mathematics arriving in computing essentially unchanged.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**15.1 ★ Build a KD-tree.** Run `build_kdtree` from Section 15.2 on the points (2,3), (5,4), (9,6), (4,7), (8,1), (7,2). Draw the resulting tree, giving each node's point and splitting axis, and sketch how the root and its children cut the plane.

<details>
<summary>Solution</summary>

- Depth 0 (axis x): sorted by x the points are (2,3), (4,7), (5,4), (7,2), (8,1), (9,6). `mid = 3`, so the root is **(7,2)**. Left gets the first three, right gets (8,1), (9,6).
- Depth 1, left (axis y): sorted by y: (2,3), (5,4), (4,7). The median is **(5,4)**, with (2,3) on its left and (4,7) on its right.
- Depth 1, right (axis y): sorted by y: (8,1), (9,6). `mid = 1`, so the node is **(9,6)** with (8,1) as its left child and no right child.
- Depth 2 (axis x): (2,3), (4,7) and (8,1) are leaves.

```
            (7,2) x
           /       \
      (5,4) y      (9,6) y
      /     \       /
  (2,3) x  (4,7) x (8,1) x
```

The root draws the vertical line x = 7. On the left half, (5,4) draws the horizontal line y = 4, separating (2,3) below from (4,7) above. On the right half, (9,6) draws y = 6, with (8,1) below it. Every node's subtree occupies a rectangle bounded by its ancestors' lines.

</details>

**15.2 ★★ Trace a nearest-neighbour search.** On the tree from 15.1, run `nearest(root, (9, 2))`. List the nodes visited in order, the best point and distance after each, and every pruning decision. Which subtree is never examined?

<details>
<summary>Hint</summary>

At each node, the pruning test compares |diff| (the distance to the splitting line) with the best distance so far.

</details>

<details>
<summary>Solution</summary>

1. **(7,2)**, axis x. Distance √(4 + 0) = 2.000; best = (7,2). diff = 9 − 7 = 2 ≥ 0, so near = right subtree (9,6), far = left subtree (5,4).
2. **(9,6)**, axis y. Distance 4.000, not better. diff = 2 − 6 = −4 < 0, so near = left (8,1), far = right (empty).
3. **(8,1)**, axis x. Distance √(1 + 1) ≈ 1.414; best = (8,1). Both children are empty.
4. Back at (9,6): is |−4| < 1.414? No. Its (empty) far side is skipped.
5. Back at (7,2): is |2| < 1.414? No. **The whole left subtree, (5,4) with (2,3) and (4,7), is pruned.**

Result: **(8,1)** at distance √2, after visiting 3 of 6 nodes. The pruning is sound: every point in the left subtree has x < 7, so it is at least 2 away from the target, which already loses to √2.

</details>

**15.3 ★★ Find the bug.** A developer "simplifies" the pruning test in `nearest` to compare against the current node's own distance:

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
    if dist(target, node.point) < dist(target, best):    # changed line
        best = nearest(far, target, best)
    return best
```

Give a small point set and query where this returns the wrong answer, and explain what the correct test measures.

<details>
<summary>Solution</summary>

Build the tree from (4,0), (5,5), (9,9): the root is (5,5) splitting on x, with (4,0) on the left and (9,9) on the right. Query (6,0).

- At the root, distance √(1 + 25) ≈ 5.10, so best = (5,5). diff = 6 − 5 = 1, so near = right.
- At (9,9), distance √(9 + 81) ≈ 9.49. Not better.
- Back at the root, the buggy test asks whether 5.10 < 5.10. It is false (the root *is* the best), so the left subtree is skipped.

The buggy version returns (5,5) at 5.10. The correct answer is (4,0), at distance 2.

The node's own distance says nothing about what lies across the splitting line. The correct test, `abs(diff) < dist(target, best)`, asks whether the circle of radius best-distance around the target crosses that line. Here |diff| = 1 < 5.10, so the circle crosses x = 5 and the left side must be searched. A KD-tree search is only correct if it prunes on the distance to the *region*, never the distance to a representative point.

</details>

**15.4 ★★ Range query on a quadtree.** The `QuadTree` in Section 15.3 shows only `insert`. Write `subdivide` and `query_range(area)`, which returns every stored point inside a query rectangle. Note that this `insert` leaves a node's original points in place when it subdivides, so internal nodes hold points too.

<details>
<summary>Hint</summary>

Two tests drive the recursion: does this node's boundary intersect the query at all (if not, prune), and is each stored point inside the query?

</details>

<details>
<summary>Solution</summary>

`boundary` needs `contains` and `intersects`, so it is a small class rather than a tuple. Using half-open boxes means a point on a shared edge belongs to exactly one child.

```python
class Rect:
    """Half-open box: x <= px < x + w and y <= py < y + h."""
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    def contains(self, p):
        return (self.x <= p[0] < self.x + self.w
                and self.y <= p[1] < self.y + self.h)

    def intersects(self, other):
        return not (other.x >= self.x + self.w or other.x + other.w <= self.x
                    or other.y >= self.y + self.h or other.y + other.h <= self.y)

class QuadTree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False

    def insert(self, point):                   # as in Section 15.3
        if not self.boundary.contains(point):
            return False
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True
        if not self.divided:
            self.subdivide()
        return (self.nw.insert(point) or self.ne.insert(point)
                or self.sw.insert(point) or self.se.insert(point))

    def subdivide(self):
        b, hw, hh = self.boundary, self.boundary.w / 2, self.boundary.h / 2
        self.sw = QuadTree(Rect(b.x, b.y, hw, hh), self.capacity)
        self.se = QuadTree(Rect(b.x + hw, b.y, hw, hh), self.capacity)
        self.nw = QuadTree(Rect(b.x, b.y + hh, hw, hh), self.capacity)
        self.ne = QuadTree(Rect(b.x + hw, b.y + hh, hw, hh), self.capacity)
        self.divided = True

    def query_range(self, area, found=None):
        if found is None:
            found = []
        if not self.boundary.intersects(area):
            return found                       # prune the whole subtree
        for p in self.points:                  # internal nodes keep points too
            if area.contains(p):
                found.append(p)
        if self.divided:
            for child in (self.nw, self.ne, self.sw, self.se):
                child.query_range(area, found)
        return found

import random
qt = QuadTree(Rect(0, 0, 100, 100))
pts = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(500)]
for p in pts:
    assert qt.insert(p)
area = Rect(20, 30, 25, 10)
assert sorted(qt.query_range(area)) == sorted(p for p in pts if area.contains(p))
```

The intersection test is the whole point: a query covering a small corner of the space descends only into the cells that touch it, and everything else is discarded at the top. Forgetting the points stored in internal nodes is the easy bug with this variant of `insert`; it silently drops the first `capacity` points of every subdivided cell.

</details>

**15.5 ★ Z-order by hand.** On an 8 × 8 grid, the Morton code interleaves the bits of x and y, with x's bits in the even positions (bit 0 of the code is bit 0 of x, bit 1 is bit 0 of y, and so on). (a) Compute the codes of (5,3), (3,3) and (4,3). (b) (3,3) and (4,3) are horizontal neighbours. A B-tree range scan over codes 15 to 26 is meant to find "cells near them". How many cells does it return, and which unwanted ones?

<details>
<summary>Solution</summary>

(a) Write each coordinate in 3 bits and interleave as y₂x₂ y₁x₁ y₀x₀:

| Point | x | y | Interleaved | Code |
|-------|---|---|-------------|------|
| (5,3) | 101 | 011 | 01 10 11 | 27 |
| (3,3) | 011 | 011 | 00 11 11 | 15 |
| (4,3) | 100 | 011 | 01 10 10 | 26 |

(b) The scan returns **12 cells**: (3,3), then (4,0), (5,0), (4,1), (5,1), (6,0), (7,0), (6,1), (7,1), (4,2), (5,2), and finally (4,3). Between two adjacent cells, the curve detours through 10 cells of the lower-right quadrant, including (6,0) and (7,0), which are three rows down and several columns across. This is the "discontinuity" Section 15.5 warns about: x = 3 to x = 4 crosses the top-level split, where the curve jumps. Production systems answer a range query with several smaller code ranges, one per curve segment, rather than one big one, and the Hilbert curve reduces (but does not eliminate) how often this happens.

</details>

**15.6 ★★ Design: a food-delivery backend.** You must support three queries: (1) "restaurants within 3 km of this customer", over 500,000 restaurants that rarely move; (2) "which delivery zone contains this address", where zones are hand-drawn polygons; (3) "the 5 nearest available couriers", over 20,000 couriers each reporting a new position every 4 seconds. Pick a structure for each and say what you are giving up.

<details>
<summary>Solution</summary>

1. **Restaurants: geohash or S2 cells in the existing database, or an R-tree index (PostGIS).** The data is static points that must live in a database and probably shard by region. Cover the 3 km circle with a handful of cells, scan those key ranges, then filter by exact distance. Given up: the cell cover over-fetches near its edges, and you must query neighbouring cells to avoid the boundary problem.
2. **Zones: R-tree.** These are extended objects, not points, which rules out KD-trees and point quadtrees. Index each polygon's bounding rectangle, use the R-tree to find candidate zones whose MBR contains the address, then run an exact point-in-polygon test on those few. Given up: overlapping MBRs mean some queries check several candidates; with few, rarely edited zones, that is cheap.
3. **Couriers: a uniform grid (or geohash/H3 cells) kept in a hash map from cell to the set of couriers.** 20,000 couriers × one update per 4 s is 5,000 updates per second, and a grid makes each update O(1): remove from the old cell, add to the new one. For k-nearest, search the courier's cell, then rings of neighbouring cells until 5 are found and the next ring cannot contain anything closer. A KD-tree is the wrong choice: it does not rebalance (Section 15.2), so it would need rebuilding constantly. Given up: the grid's cell size is fixed, so dense downtown cells hold many couriers and sparse suburbs need several rings of empty cells. That is acceptable at this scale, and per-city grid sizes or hierarchical H3 resolutions fix it if it is not.

</details>

**15.7 ★★★ Where O(√n) comes from.** Section 15.2 gives a KD-tree range query as O(n^(1−1/k) + m). Prove the 2D case: in a balanced KD-tree over n points (with distinct coordinates), any vertical line intersects the regions of only O(√n) nodes. Then explain how that gives O(√n + m) for an axis-aligned rectangle query reporting m points, and how the argument generalises to n^(1−1/k).

<details>
<summary>Hint</summary>

Look two levels at a time. A vertical line meets one child of an x-splitting node, but both children of a y-splitting node.

</details>

<details>
<summary>Solution</summary>

**The line bound.** Let Q(n) be the number of nodes whose regions a vertical line ℓ meets, in a subtree with n points whose root splits on x.

- The root's vertical split line puts ℓ on one side, so ℓ enters only one child (n/2 points, splitting on y).
- That child splits horizontally, and a vertical line crosses a horizontal split, so ℓ enters **both** grandchildren, each with about n/4 points and splitting on x again.

So Q(n) ≤ 2 + 2Q(n/4) (the 2 counts the root and the one child). Unrolling over log₄ n levels gives a geometric sum dominated by its last term: Q(n) = O(2^(log₄ n)) = O(n^(1/2)) = **O(√n)**. Starting from a y-splitting root only adds one level. A horizontal line is symmetric.

**The range query.** Every node a rectangle query visits is one of:

- **fully inside** the rectangle: report its whole subtree, O(size of subtree), paid for by the output m;
- **disjoint** from it: never visited, because its parent pruned it;
- **crossing the boundary**: then the node's region meets one of the rectangle's four edges, and each edge lies on a vertical or horizontal line.

By the line bound, each of the four lines meets O(√n) regions, so at most O(√n) boundary nodes are visited. The parents of pruned or fully-inside nodes are themselves boundary nodes, so they add at most a constant factor. Total: **O(√n + m)**.

**In k dimensions,** the boundary is made of hyperplanes. A hyperplane perpendicular to one axis enters one child at the level splitting on that axis and both children at each of the other k − 1 levels, so k levels cover 2^(k−1) subtrees of n/2^k points: Q(n) = 2^(k−1) Q(n/2^k) + O(2^k), which solves to O(n^((k−1)/k)) = **O(n^(1−1/k))**. At k = 10 this is n^0.9, barely better than scanning everything, which is the curse of dimensionality showing up in the bound itself.

</details>

---

## Where this connects

- [Chapter 16: External Memory and Cache-Oblivious Structures](ch16-external-memory-and-cache-oblivious-structures.md). Why KD-trees degrade once the data leaves cache
- [Chapter 19: Emerging and Specialized Structures](ch19-emerging-and-specialized-structures.md). HNSW and the high-dimensional case these structures cannot handle
