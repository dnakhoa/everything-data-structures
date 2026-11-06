# Chapter 11: Graphs—Modeling Relationships

Every structure in Volume I imposes a shape on its data: a line (arrays, lists), a hierarchy (trees), a partial order (heaps). A graph imposes nothing. It records only *which things are related to which*, and that generality is why it shows up everywhere: road networks, package dependencies, social networks, the call graph of a program, the links between web pages, the routers of the internet.

The price of generality is that there is no single "graph data structure". There are several representations, each good at different questions, and a family of algorithms that are really just the right auxiliary structure (a queue, a stack, a heap, a union-find) driven over the graph. This chapter is as much about those pairings as about graphs themselves.

## 11.1 Graph Fundamentals

A graph G = (V, E) consists of:
- V: a set of vertices (also called nodes)
- E: a set of edges, each connecting a pair of vertices

```
Graph Example:
V = {A, B, C, D, E}
E = {(A,B), (A,C), (B,D), (C,D), (D,E)}

      A
     / \
    B   C
     \ /
      D───E
```

We write n = |V| and m = |E|, or simply V and E inside O(...). The vocabulary you need:

- **Adjacent**: u and v are adjacent if (u, v) ∈ E. They are each other's **neighbours**.
- **Degree** of v: the number of edges touching v. In a directed graph this splits into **in-degree** (edges arriving) and **out-degree** (edges leaving). In the example, deg(D) = 3.
- **Path**: a sequence of vertices where each consecutive pair is an edge. Its **length** is the number of edges.
- **Cycle**: a path of length at least 1 (at least 3 in a simple undirected graph) that starts and ends at the same vertex. A-B-D-C-A is a cycle of length 4.
- **Connected**: an undirected graph is connected if every vertex can reach every other. A directed graph is **strongly connected** if every vertex can reach every other following edge directions.

Two counting facts are worth memorising because they drive every complexity bound in this chapter:

1. **Handshake lemma.** In an undirected graph, the degrees sum to 2E, because every edge contributes to the degree of both its endpoints. The example has degrees 2+2+2+3+1 = 10 = 2 × 5.
2. **Edge bound.** A simple undirected graph has at most V(V-1)/2 edges, so E = O(V²) and log E = O(log V). A graph is **sparse** when E is close to V (road networks: most intersections have degree ≤ 4) and **dense** when E is close to V² (a complete graph of all-pairs distances).

## 11.2 Graph Types

**Directed vs. undirected:**
- Undirected: edges have no direction (relationships are symmetric: "is married to")
- Directed: edges have direction, A → B does not imply B → A ("follows", "depends on", "links to")

**Weighted vs. unweighted:**
- Weighted: edges carry a number (distance, cost, latency, capacity)
- Unweighted: every edge counts as 1

**Simple vs. multigraph:**
- Simple: no self-loops, at most one edge between any pair
- Multigraph: parallel edges allowed (two flights between the same cities at different prices)

**Cyclic vs. acyclic:**
- Cyclic: contains at least one cycle
- Acyclic: no cycles. A connected acyclic undirected graph is a **tree** (exactly V - 1 edges). A directed acyclic graph is a **DAG**.

**Bipartite:** the vertices split into two sides with every edge crossing between them (students and courses, users and products). A graph is bipartite exactly when it has no odd-length cycle.

## 11.3 Graph Representations

Throughout this chapter, Python examples use an adjacency list stored as a dict: `graph[u]` is a list of u's neighbours, or a list of `(neighbour, weight)` pairs for weighted graphs. The example graph from 11.1 is:

```python
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D'],
    'D': ['B', 'C', 'E'],
    'E': ['D'],
}
```

### Adjacency Matrix

A V×V matrix where `adj[i][j]` records whether (or with what weight) an edge i → j exists:

```c
// For weighted graph
int adj[V][V];
// adj[i][j] = weight if edge exists, INF otherwise
```

```
Undirected Graph:
     A  B  C  D  E
   ┌───────────────
 A │ 0  1  1  0  0
 B │ 1  0  0  1  0
 C │ 1  0  0  1  0
 D │ 0  1  1  0  1
 E │ 0  0  0  1  0

Space: O(V²)
```

For an undirected graph the matrix is symmetric. **Pros**: O(1) "is there an edge u-v?", trivial to implement, and matrix algebra applies (entry (i, j) of A^k counts walks of length k from i to j). **Cons**: O(V²) space and O(V) to list a vertex's neighbours, even if it has only one. A road network of 10 million intersections would need 10^14 cells.

### Adjacency List

Each vertex stores the list of its neighbours:

```c
struct Node {
    int vertex;
    struct Node *next;
};

struct Graph {
    int V;
    struct Node **adj;
};
```

```
Adjacency List:
A → [B] → [C] → NULL
B → [A] → [D] → NULL
C → [A] → [D] → NULL
D → [B] → [C] → [E] → NULL
E → [D] → NULL

Space: O(V + E)
```

**Pros**: O(V + E) space, and iterating over a vertex's neighbours costs O(degree), which is what traversals need. **Cons**: "is there an edge u-v?" costs O(deg(u)) unless you store neighbour *sets* (hash sets) instead of lists, which buys O(1) expected lookup at a constant-factor memory cost.

In practice, use dynamic arrays rather than linked lists for the neighbour lists. Chapter 3's argument about cache locality applies directly: scanning a contiguous array of neighbour IDs is several times faster than chasing pointers.

### Edge List

Just a list of `(u, v)` or `(weight, u, v)` tuples. Useless for traversal (finding a vertex's neighbours means scanning everything), but it is the natural input for algorithms that look at edges in a global order: Kruskal's MST sorts it, and Bellman-Ford sweeps it repeatedly.

### Compressed Sparse Row (CSR)

When the graph is static, flatten the adjacency lists into two arrays: `targets` holds every neighbour list concatenated, and `offsets[u]` says where u's list starts. The neighbours of u are `targets[offsets[u] : offsets[u+1]]`.

```
Vertex index:  A=0  B=1  C=2  D=3  E=4

offsets: [0, 2, 4, 6, 9, 10]
targets: [B, C,  A, D,  A, D,  B, C, E,  D]
          └─A─┘  └─B─┘  └─C─┘  └──D───┘  └E┘
```

CSR uses exactly V + 1 + E integers with no per-node pointers, and every traversal is a sequential scan. It is the standard layout in graph analytics libraries, sparse matrix code (the matrix *is* the graph), and GPU graph processing. The cost is that adding an edge means rebuilding the arrays.

### Choosing a representation

| Question | Matrix | Adjacency list | Edge list | CSR |
|----------|--------|----------------|-----------|-----|
| Space | O(V²) | O(V + E) | O(E) | O(V + E) |
| Is (u, v) an edge? | O(1) | O(deg u), O(1) expected with sets | O(E) | O(deg u), O(log deg u) if sorted |
| List neighbours of u | O(V) | O(deg u) | O(E) | O(deg u) |
| Add an edge | O(1) | O(1) amortized | O(1) amortized | O(V + E) rebuild |
| Best for | dense graphs, Floyd-Warshall | general purpose, mutable graphs | Kruskal, Bellman-Ford | large static graphs |

## 11.4 Graph Traversal

Both basic traversals have the same skeleton: keep a set of discovered vertices and a container of vertices waiting to be processed. The container decides everything. A **queue** gives breadth-first search; a **stack** gives depth-first search.

### Breadth-First Search (BFS)

BFS explores vertices in waves: first the source, then everything at distance 1, then everything at distance 2, and so on. Because a vertex is first discovered along a shortest path, recording *who discovered it* gives you shortest paths in an unweighted graph for free:

```python
from collections import deque

def bfs(graph, source):
    """Return (dist, parent) for every vertex reachable from source."""
    dist = {source: 0}
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in dist:            # first discovery is the shortest
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return dist, parent


def reconstruct_path(parent, target):
    if target not in parent:
        return None                      # unreachable
    path = []
    while target is not None:
        path.append(target)
        target = parent[target]
    return path[::-1]
```

On the example graph, `bfs(graph, 'A')` gives distances A:0, B:1, C:1, D:2, E:3, and `reconstruct_path(parent, 'E')` returns `['A', 'B', 'D', 'E']`.

Mark a vertex as discovered when you *enqueue* it, not when you dequeue it. Marking on dequeue lets the same vertex enter the queue many times (once per neighbour that sees it before it is processed), which is still correct but wastes up to O(E) queue space.

Properties:
- Uses a queue (FIFO), Chapter 5
- Finds shortest paths (fewest edges) in unweighted graphs
- Time: O(V + E). Each vertex is enqueued once and each adjacency list is scanned once; by the handshake lemma the scans total O(E).
- Space: O(V)

### Depth-First Search (DFS)

DFS follows one path as deep as it can, then backtracks:

```python
def dfs_recursive(graph, u, visited=None, order=None):
    if visited is None:
        visited, order = set(), []
    visited.add(u)
    order.append(u)
    for v in graph[u]:
        if v not in visited:
            dfs_recursive(graph, v, visited, order)
    return order


def dfs_iterative(graph, start):
    visited, order = set(), []
    stack = [start]
    while stack:
        u = stack.pop()
        if u in visited:
            continue                     # a vertex can be pushed more than once
        visited.add(u)
        order.append(u)
        # push in reverse so neighbours are visited in listed order
        for v in reversed(graph[u]):
            if v not in visited:
                stack.append(v)
    return order
```

Both return `['A', 'B', 'D', 'C', 'E']` on the example graph. Two details in the iterative version matter. First, it checks `visited` when *popping*, unlike BFS, because a vertex may be pushed several times before it is reached, and only the last push reflects true depth-first order. Second, it pushes neighbours in reverse; without that, it still visits everything but in a different order from the recursive version, which surprises people when comparing outputs.

The recursive version is shorter, but its call stack is the DFS stack. Python's default recursion limit is 1000, so a path-shaped graph of 10,000 vertices crashes it. Use the iterative form (or raise the limit with care) for large inputs.

Properties:
- Uses a stack (LIFO), explicit or the call stack
- Time: O(V + E); Space: O(V)
- Does *not* find shortest paths. Its value is the structure it reveals, which the next section uses.

To traverse a graph that is not connected, run the traversal from every vertex not yet visited. Each run discovers one **connected component**, so counting runs counts components.

## 11.5 What DFS Reveals: Cycles and Bipartiteness

### Cycle detection in directed graphs

During a DFS, each vertex is in one of three states, traditionally coloured:

- **White**: not yet discovered
- **Gray**: discovered, still on the current recursion path (its descendants are being explored)
- **Black**: finished, all descendants explored

An edge u → v where v is gray points back to an ancestor of u on the current path. That is a **back edge**, and a directed graph has a cycle *if and only if* DFS finds a back edge.

```python
WHITE, GRAY, BLACK = 0, 1, 2

def has_cycle(graph):
    color = {u: WHITE for u in graph}

    def visit(u):
        color[u] = GRAY                  # on the current DFS path
        for v in graph[u]:
            if color[v] == GRAY:         # back edge: v is an ancestor of u
                return True
            if color[v] == WHITE and visit(v):
                return True
        color[u] = BLACK                 # finished
        return False

    return any(color[u] == WHITE and visit(u) for u in graph)
```

Two colours are not enough. With only "visited / not visited", an edge to a vertex finished in an earlier branch (a **cross edge**, harmless) looks the same as an edge to an ancestor (a back edge, a cycle). In the diamond A → B, A → C, B → D, C → D, the edge C → D reaches an already-visited D, but there is no cycle. D is black, not gray.

(For undirected graphs, it is simpler: any edge to an already-visited vertex other than your DFS parent closes a cycle. Or use union-find, 11.8.)

### Bipartiteness

Two-colour the graph with BFS: give the source side 0, each newly discovered neighbour the opposite side of its discoverer. If you ever find an edge whose endpoints already have the same side, the graph has an odd cycle and is not bipartite.

```python
def is_bipartite(graph):
    side = {}
    for s in graph:                      # handle every component
        if s in side:
            continue
        side[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if v not in side:
                    side[v] = 1 - side[u]
                    queue.append(v)
                elif side[v] == side[u]:
                    return False         # edge inside one side: odd cycle
    return True
```

The example graph is bipartite: {A, D} on one side, {B, C, E} on the other. Adding the edge B-C creates the triangle A-B-C and breaks it.

## 11.6 Topological Sort

A topological order of a DAG lists the vertices so that every edge points forward: if u → v, then u comes before v. It answers "in what order can I do these tasks, given their dependencies?" A topological order exists exactly when the graph has no directed cycle.

**Kahn's algorithm** repeatedly removes a vertex with no remaining incoming edges:

```python
def topological_sort(graph):
    """Kahn's algorithm. Returns an order, or None if the graph has a cycle."""
    in_degree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] += 1

    queue = deque(u for u in graph if in_degree[u] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    return order if len(order) == len(graph) else None
```

The final check is the cycle detector. Vertices on a cycle never reach in-degree 0 (each waits on another), so they never get output. If the order is shorter than V, the leftover vertices contain a cycle. A version that omits this check silently returns a partial order for cyclic input, which is a real bug in build tools.

Time: O(V + E). Use `deque.popleft()`, not `list.pop(0)`; the latter shifts the whole list and makes the loop O(V²) in the worst case.

**The DFS method** is a one-line consequence of 11.5: in a DAG, a vertex finishes (turns black) only after everything reachable from it has finished. So the *reverse of finishing order* is a topological order.

```python
def topological_sort_dfs(graph):
    """Reverse postorder. Assumes the graph is a DAG."""
    visited, postorder = set(), []

    def visit(u):
        visited.add(u)
        for v in graph[u]:
            if v not in visited:
                visit(v)
        postorder.append(u)              # u finishes after everything it reaches

    for u in graph:
        if u not in visited:
            visit(u)
    return postorder[::-1]
```

Worked example (getting dressed):

```python
dag = {
    'socks':  ['shoes'],
    'pants':  ['shoes', 'belt'],
    'shirt':  ['tie', 'belt'],
    'tie':    ['jacket'],
    'belt':   ['jacket'],
    'shoes':  [],
    'jacket': [],
}
# Kahn:  socks, pants, shirt, shoes, tie, belt, jacket
```

Topological orders are rarely unique. Any order that respects the edges is correct, which is why two correct implementations can disagree.

Applications: build systems (make, Bazel), package managers resolving install order, spreadsheet recalculation, course prerequisites, scheduling the layers of a neural network's computation graph, and instruction scheduling in compilers.

## 11.7 Strongly Connected Components

In a directed graph, u and v are in the same **strongly connected component** (SCC) if each can reach the other. SCCs partition the vertices, and if you shrink each SCC to a single vertex, what remains (the **condensation**) is always a DAG. That makes SCCs the standard first step for problems on general directed graphs: collapse the cycles, then work on a DAG.

**Kosaraju's algorithm** uses two DFS passes:

1. Run DFS on G and record vertices in order of finishing time.
2. Build the **transpose** Gᵀ (every edge reversed).
3. Run DFS on Gᵀ, starting each new search from the unassigned vertex that finished *latest* in pass 1. Each search collects exactly one SCC.

```python
def strongly_connected_components(graph):
    # Pass 1: record finishing order on the original graph.
    visited, finish = set(), []

    def visit(u):
        visited.add(u)
        for v in graph[u]:
            if v not in visited:
                visit(v)
        finish.append(u)

    for u in graph:
        if u not in visited:
            visit(u)

    # Build the transpose (every edge reversed).
    transpose = {u: [] for u in graph}
    for u in graph:
        for v in graph[u]:
            transpose[v].append(u)

    # Pass 2: DFS on the transpose in decreasing finish time.
    assigned, components = set(), []

    def collect(u, comp):
        assigned.add(u)
        comp.append(u)
        for v in transpose[u]:
            if v not in assigned:
                collect(v, comp)

    for u in reversed(finish):
        if u not in assigned:
            comp = []
            collect(u, comp)
            components.append(comp)
    return components
```

Why it works: the vertex that finishes last lies in a "source" SCC of the condensation (nothing outside it reaches in). Reversing the edges turns that source into a sink, so a DFS from it in Gᵀ cannot leak out of its own component. Removing that component exposes the next one, and so on.

**Tarjan's algorithm** finds the same components in a single DFS by tracking, for each vertex, the lowest discovery time reachable through its subtree (its "low-link"). It avoids building the transpose and is usually faster in practice; Kosaraju is easier to remember and to prove. Both run in O(V + E).

Uses: finding dependency cycles in module graphs, solving 2-SAT (a formula is satisfiable iff no variable shares an SCC with its negation), and finding the "core" of a web or social graph.

## 11.8 Union-Find (Disjoint Set Union)

Union-find maintains a partition of {0, ..., n-1} into disjoint sets under two operations: `find(x)` returns a representative of x's set, and `union(x, y)` merges two sets. It answers "are x and y connected?" while edges are being *added*, which is exactly what Kruskal's algorithm needs.

Each set is a tree of parent pointers; the root is the representative.

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False                 # already in the same set
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx             # union by rank: shorter tree goes under
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True
```

Two independent optimisations make it fast:

- **Union by rank** attaches the shorter tree under the taller one, so trees stay O(log n) tall even without compression.
- **Path compression** makes every node on a `find` path point directly at the root, flattening the tree for future calls.

With both, any sequence of m operations takes O(m α(n)) time, where α is the inverse Ackermann function. α(n) ≤ 4 for any n that fits in the physical universe, so this is constant in practice, though not in theory: Fredman and Saks proved in 1989 that no union-find structure can do better. Either optimisation alone gives O(log n) amortized per operation.

What union-find *cannot* do is split sets. Deleting an edge requires a different structure (or, offline, the DSU-with-rollback technique from Chapter 23).

## 11.9 Minimum Spanning Trees

A **spanning tree** of a connected, undirected, weighted graph is a subset of V - 1 edges that connects every vertex without cycles. A **minimum spanning tree** (MST) is one with the least total weight: the cheapest way to wire up a set of buildings, cities or circuit pins.

Both classic algorithms are greedy, and both are justified by one fact:

> **Cut property.** Split the vertices into any two non-empty groups. The lightest edge crossing between the groups belongs to some MST. (If edge weights are distinct, it belongs to *the* MST, which is then unique.)

Proof sketch: take an MST that does not contain that lightest crossing edge e. Adding e creates a cycle, and the cycle must cross the cut a second time through some edge f with weight ≥ weight(e). Swap f for e: still a spanning tree, no heavier. So some MST contains e.

### Kruskal's Algorithm

Sort all edges by weight; take each edge unless it would form a cycle. Union-find is the cycle detector: an edge (u, v) forms a cycle exactly when u and v are already in the same set.

```python
def kruskal(n, edges):
    """n vertices numbered 0..n-1; edges is a list of (weight, u, v)."""
    uf = UnionFind(n)
    mst = []
    for w, u, v in sorted(edges):
        if uf.union(u, v):               # False means u and v already connected
            mst.append((u, v, w))
            if len(mst) == n - 1:
                break
    return mst
```

Each accepted edge is the lightest edge leaving the component it joins, so the cut property applies. Time: O(E log E) for the sort, which is the same as O(E log V) since E ≤ V². The union-find work is nearly linear and never dominates. If the graph is disconnected, Kruskal returns a minimum spanning *forest* with fewer than n - 1 edges.

### Prim's Algorithm

Grow a single tree from a start vertex, always adding the cheapest edge that leaves it. A min-heap (Chapter 9) holds the candidate edges:

```python
import heapq

def prim(graph, start):
    """graph[u] is a list of (v, weight) pairs, undirected."""
    visited = {start}
    mst = []
    heap = [(w, start, v) for v, w in graph[start]]
    heapq.heapify(heap)

    while heap and len(visited) < len(graph):
        w, u, v = heapq.heappop(heap)
        if v in visited:
            continue                     # stale entry: v was reached more cheaply
        visited.add(v)
        mst.append((u, v, w))
        for x, wx in graph[v]:
            if x not in visited:
                heapq.heappush(heap, (wx, v, x))
    return mst
```

The cut is "tree vertices vs. everything else", and the heap's minimum is the lightest crossing edge. Instead of decreasing keys, this version pushes duplicates and discards stale ones when popped ("lazy deletion"), which keeps the code simple and works with Python's `heapq`, which has no decrease-key.

Time: O(E log V) with a binary heap. With a Fibonacci heap it is O(E + V log V), better on paper for dense graphs; see Chapter 19 for why that rarely wins in practice. For truly dense graphs stored as a matrix, the simple O(V²) array version of Prim (scan for the minimum each round, no heap) is the fastest option.

**Which one?** Kruskal is simplest when you already have an edge list, and it handles disconnected graphs naturally. Prim suits dense graphs and adjacency structures. Both give the same total weight.

## 11.10 Shortest Paths

The single-source problem: given a source s, find the minimum-weight path from s to every other vertex. Which algorithm you can use depends entirely on the edge weights.

### Single-Source, Non-Negative Weights: Dijkstra's Algorithm

Dijkstra's algorithm is BFS with a priority queue in place of the FIFO queue: always expand the unfinished vertex with the smallest known distance.

```python
import heapq

def dijkstra(graph, source):
    """graph[u] is a list of (v, weight) pairs with weight >= 0."""
    dist = {u: float('inf') for u in graph}
    parent = {source: None}
    dist[source] = 0
    pq = [(0, source)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue                     # stale entry (lazy deletion)
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                parent[v] = u
                heapq.heappush(pq, (dist[v], v))
    return dist, parent
```

The operation `dist[v] = min(dist[v], dist[u] + w)` is called **relaxing** the edge u → v. Every shortest-path algorithm in this section is a strategy for choosing which edges to relax, in which order.

**Worked trace.** Edges: S→A (4), S→B (1), B→A (2), A→C (1), B→C (5), C→D (3).

| Step | Pop | Relaxations | Heap afterwards |
|------|-----|-------------|-----------------|
| 1 | (0, S) | A: ∞→4, B: ∞→1 | (1,B) (4,A) |
| 2 | (1, B) | A: 4→3, C: ∞→6 | (3,A) (4,A) (6,C) |
| 3 | (3, A) | C: 6→4 | (4,A) (4,C) (6,C) |
| 4 | (4, A) | stale (4 > dist[A] = 3), skip | (4,C) (6,C) |
| 5 | (4, C) | D: ∞→7 | (6,C) (7,D) |
| 6 | (6, C) | stale, skip | (7,D) |
| 7 | (7, D) | none | empty |

<figure>
{{#include ../images/dijkstra-trace.svg}}
<figcaption>The graph from the trace. Blue edges are the parent pointers Dijkstra leaves behind; together they form a tree of shortest paths from S.</figcaption>
</figure>

Result: S:0, B:1, A:3, C:4, D:7, with path S → B → A → C → D. Note that A was first reached directly (cost 4) and improved via B; the direct edge was not the shortest route.

**Why it is correct.** When a vertex u is popped with its true distance, every vertex still in the heap has a distance at least as large. Any path to u through one of those vertices therefore costs at least as much, *because edges cannot make a path cheaper*. So u's distance is final.

**Why negative edges break it.** That last sentence is the whole assumption. Take S→A (1), S→B (5), B→A (-10), A→C (1). Textbook Dijkstra finalises A at distance 1 when it pops it, then finalises C at 2. Only then does it pop B and discover that S → B → A costs -5. A was already declared done, so A and C end up wrong (the true distances are -5 and -4).

The lazy-deletion code above happens to recover in this example, because it re-pushes A when A improves and processes it again. That does not rescue it in general: with negative edges, a vertex can be reprocessed many times, and there are graphs that force exponentially many repetitions. If weights can be negative, use Bellman-Ford.

Time: O((V + E) log V) with a binary heap; O(E + V log V) with a Fibonacci heap.

**A\* search** is Dijkstra with a priority of `dist[v] + h(v)`, where h estimates the remaining distance to a single target (straight-line distance in a road map, for example). If h never overestimates the true remaining distance (straight-line distance never does), A\* still finds the shortest path, but it explores far fewer vertices because it is pulled toward the goal. It is the standard algorithm for pathfinding in games and robotics.

### Single-Source, Any Weights: Bellman-Ford

Bellman-Ford drops the cleverness and relaxes *every* edge, V - 1 times:

```python
def bellman_ford(vertices, edges, source):
    """edges is a list of (u, v, weight). Returns dist, or None on a negative cycle."""
    dist = {u: float('inf') for u in vertices}
    dist[source] = 0
    for _ in range(len(vertices) - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break                        # converged early
    for u, v, w in edges:                # a V-th improvement means a negative cycle
        if dist[u] + w < dist[v]:
            return None
    return dist
```

Why V - 1 rounds: a shortest path without cycles has at most V - 1 edges, and after round k, every vertex whose shortest path uses at most k edges has its correct distance (by induction: round k relaxes the k-th edge of that path). If anything still improves in round V, some path is getting cheaper without bound, so there is a **negative cycle** reachable from the source and "shortest path" is undefined.

Time: O(VE). That is much slower than Dijkstra, but it handles negative weights and detects negative cycles. It is also naturally distributed, since each relaxation only needs a neighbour's current estimate. That is why distance-vector routing protocols such as RIP are Bellman-Ford running across routers (Chapter 28). A classic application of negative-cycle detection: currency arbitrage. With edge weights -log(rate), a negative cycle is a sequence of trades that ends with more money than it started.

### All-Pairs: Floyd-Warshall

To get the distance between *every* pair of vertices, Floyd-Warshall uses dynamic programming over intermediate vertices. After processing k, `dist[i][j]` is the shortest path from i to j that uses only vertices 0..k as intermediate stops.

```python
def floyd_warshall(n, edges):
    """n vertices numbered 0..n-1; edges is a list of (u, v, weight)."""
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)  # keep the cheapest parallel edge

    for k in range(n):                   # allow k as an intermediate vertex
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist   # dist[i][i] < 0 for some i means a negative cycle
```

The loop order matters: k must be the *outermost* loop. Putting it innermost gives code that looks identical and returns wrong answers.

Time: O(V³), Space: O(V²). It handles negative edges (not negative cycles), and its three tight loops over a matrix are very cache-friendly, so for a few hundred vertices it often beats running Dijkstra V times despite the worse bound. For large sparse graphs, V runs of Dijkstra (O(VE log V)) win. With negative edges, Johnson's algorithm runs Bellman-Ford once to reweight all edges to be non-negative, then runs Dijkstra from every vertex.

### Choosing a shortest-path algorithm

| Situation | Algorithm | Time |
|-----------|-----------|------|
| Unweighted | BFS | O(V + E) |
| Weights only 0 or 1 | 0-1 BFS (deque: push 0-edges to the front, 1-edges to the back) | O(V + E) |
| DAG, any weights | Relax edges in topological order | O(V + E) |
| Non-negative weights | Dijkstra | O((V + E) log V) |
| Non-negative, single target, good heuristic | A\* | Problem-dependent, usually far less than Dijkstra |
| Negative weights, single source | Bellman-Ford | O(VE) |
| All pairs, small or dense graph | Floyd-Warshall | O(V³) |
| All pairs, large sparse graph | V × Dijkstra (Johnson's if negative edges) | O(VE log V) |

## 11.11 Applications

- **Maps and navigation**: road networks are sparse weighted graphs. Production routers use Dijkstra variants with heavy preprocessing (contraction hierarchies) to answer continent-scale queries in milliseconds.
- **Internet routing**: link-state protocols (OSPF, IS-IS) run Dijkstra on each router's view of the topology; distance-vector protocols run distributed Bellman-Ford. Chapter 28 covers both.
- **Build and package systems**: dependency graphs are DAGs, scheduled by topological sort; cycle detection produces the "circular dependency" error.
- **Social networks**: BFS gives degrees of separation; friend suggestions start from vertices at distance 2.
- **The web**: crawlers are BFS over links; PageRank is a random walk on the link graph.
- **Compilers**: control-flow graphs, call graphs, and SCC detection for finding mutually recursive functions.
- **Garbage collection**: the mark phase of a tracing collector is a graph traversal from the roots; unreachable objects are garbage.
- **Image processing**: pixels are vertices of a grid graph; flood fill is BFS or DFS; Kruskal-style merging underlies some image segmentation.
- **Finance**: fraud detection on transaction graphs; arbitrage detection via negative cycles.

## 11.12 Historical Context

Graph theory starts with Leonhard Euler's 1736 paper on the **Seven Bridges of Königsberg**, which proved that no walk crosses each bridge exactly once. The argument (a vertex in the middle of such a walk needs even degree) is the handshake lemma in disguise.

The algorithms in this chapter come mostly from the 1950s, when telephone networks, operations research and the first computers made them practical problems:

- **BFS**: Konrad Zuse described it in 1945 (in his unpublished PhD work); Edward Moore rediscovered it in 1959 for finding the shortest path out of a maze.
- **DFS** as a maze-solving method dates to Charles Pierre Trémaux in the 19th century. Its power as an algorithmic tool, through discovery and finishing times, was established by John Hopcroft and Robert Tarjan in the early 1970s; their work won the 1986 Turing Award.
- **Kruskal's algorithm**: Joseph Kruskal, 1956. **Prim's algorithm**: Robert Prim, 1957, though Vojtěch Jarník had published it in 1930, and Otakar Borůvka had solved the MST problem in 1926 to plan an electrical network in Moravia.
- **Dijkstra's algorithm**: Edsger Dijkstra designed it in 1956, reportedly in about twenty minutes at a café in Amsterdam, and published it in 1959.
- **Bellman-Ford**: Lester Ford (1956) and Richard Bellman (1958), with Edward Moore independently.
- **Floyd-Warshall**: Robert Floyd and Stephen Warshall, both 1962 (Bernard Roy had published it in 1959).
- **Topological sort**: Arthur Kahn, 1962.
- **SCCs**: Tarjan's algorithm, 1972; Kosaraju's (unpublished, 1978) was published independently by Micha Sharir in 1981.
- **Union-find**: Bernard Galler and Michael Fischer, 1964. Tarjan's 1975 analysis showed the inverse-Ackermann bound.
- **A\***: Peter Hart, Nils Nilsson and Bertram Raphael, 1968, for the Shakey robot at SRI.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**11.1 ★ Choosing a representation.** For each graph, pick adjacency matrix, adjacency list or CSR, and justify it in one sentence: (a) a road network of 20 million intersections that is loaded once and queried millions of times; (b) a 300-city graph with a known distance between every pair; (c) a social network where users add and remove friends continuously.

<details>
<summary>Solution</summary>

(a) **CSR.** The graph is huge and sparse (average degree around 2 to 4) and never changes during queries, so the compact, cache-friendly layout pays off and the rebuild cost never matters. A matrix would need 4 × 10^14 cells.

(b) **Adjacency matrix.** The graph is complete, so E = V² anyway and the matrix wastes nothing. 90,000 cells is tiny, and O(1) edge lookup plus Floyd-Warshall's matrix loops are a natural fit.

(c) **Adjacency list, with hash sets for neighbours.** It is sparse and constantly mutated; CSR would need rebuilding on every change, and sets give O(1) expected "are these two friends?" and O(1) expected removal.

</details>

**11.2 ★ Trace BFS.** Using the adjacency-list order given, run `bfs` from vertex 1 on this undirected graph and give the `dist` and `parent` of every vertex, then the path to 6.

```python
g = {1: [2, 3], 2: [1, 4, 5], 3: [1, 5], 4: [2, 6], 5: [2, 3, 6], 6: [4, 5]}
```

<details>
<summary>Solution</summary>

Queue evolution: [1] → pop 1, discover 2, 3 → pop 2, discover 4, 5 → pop 3 (5 already discovered) → pop 4, discover 6 → pop 5, pop 6.

| Vertex | 1 | 2 | 3 | 4 | 5 | 6 |
|--------|---|---|---|---|---|---|
| dist | 0 | 1 | 1 | 2 | 2 | 3 |
| parent | None | 1 | 1 | 2 | 2 | 4 |

Path to 6: 1 → 2 → 4 → 6. The path 1 → 2 → 5 → 6 has the same length; BFS returns the one through 4 because 4 was discovered first and so discovered 6 first.

</details>

**11.3 ★★ Two colours are not enough.** A student detects directed cycles with plain DFS and a single `visited` set, reporting a cycle whenever an edge reaches a visited vertex. Give the smallest graph you can on which this reports a cycle that does not exist, and explain what the three-colour version does differently.

<details>
<summary>Hint</summary>

The false alarm needs an edge into a vertex that was fully explored on an *earlier* branch.

</details>

<details>
<summary>Solution</summary>

Three vertices suffice: A → B, A → C, C → B. DFS from A visits B (finishes it), returns, visits C, then sees C → B with B already visited, and reports a cycle. There is none.

In the three-colour version, B is **black** (finished) by then, not gray. Only an edge to a **gray** vertex (an ancestor still on the recursion stack) is a back edge, and only back edges indicate cycles. C → B is a cross edge and is ignored.

</details>

**11.4 ★★ Dijkstra by hand.** Run Dijkstra from S on the undirected graph with edges S-A (7), S-B (2), B-A (3), B-C (8), A-C (1), C-D (2), A-D (6). List vertices in the order they are finalised with their distances, and give the shortest path to D.

<details>
<summary>Solution</summary>

| Finalised | Distance | Relaxations performed |
|-----------|----------|----------------------|
| S | 0 | A → 7, B → 2 |
| B | 2 | A: 7 → 5, C → 10 |
| A | 5 | C: 10 → 6, D → 11 |
| C | 6 | D: 11 → 8 |
| D | 8 | none |

Shortest path to D: S → B → A → C → D, cost 2 + 3 + 1 + 2 = 8. Neither the direct-looking A-D edge nor the S-A edge is used.

</details>

**11.5 ★★ The k-loop.** A programmer "optimises" Floyd-Warshall by moving the `k` loop to be innermost (`for i: for j: for k:`). Construct a small graph on which it returns a wrong distance, and explain why the original order is correct.

<details>
<summary>Hint</summary>

With k innermost, `dist[i][j]` is finalised using values `dist[i][k]` and `dist[k][j]` that may not have been computed yet.

</details>

<details>
<summary>Solution</summary>

Take four vertices with edges 0→1 (1), 1→3 (1), 3→2 (1), so the only path from 0 to 2 is 0 → 1 → 3 → 2 with cost 3.

With k innermost, row 0 is finished before row 1 is touched, and within row 0 the pair (0, 2) is finished before (0, 3). So when (0, 2) is computed, the two candidates that could lead to the answer are both still ∞: `dist[0][1] + dist[1][2]` needs `dist[1][2]` (row 1, not processed yet), and `dist[0][3] + dist[3][2]` needs `dist[0][3]` (column 3, processed later in this row). `dist[0][2]` is left at ∞ and never revisited, even though a path exists. The correct version returns 3.

The correct order maintains an invariant: after the k-th outer iteration, `dist[i][j]` is the shortest path using only intermediates from {0, ..., k}. A shortest path that uses k as an intermediate splits into an i→k part and a k→j part, each using only intermediates below k, and those values were completed in earlier iterations. Moving k inward destroys that invariant.

</details>

**11.6 ★★ Kruskal with union-find.** Run Kruskal on vertices 0 to 5 with edges (weight, u, v): (4,0,1), (1,1,2), (3,0,2), (2,2,3), (5,1,3), (6,3,4), (2,4,5), (7,3,5). List each edge as accepted or rejected, and give the MST weight.

<details>
<summary>Solution</summary>

Sorted order (ties broken by u, then v, as Python's tuple sort does):

| Edge | Decision | Sets afterwards |
|------|----------|-----------------|
| (1, 1, 2) | accept | {1,2} |
| (2, 2, 3) | accept | {1,2,3} |
| (2, 4, 5) | accept | {1,2,3} {4,5} |
| (3, 0, 2) | accept | {0,1,2,3} {4,5} |
| (4, 0, 1) | reject: 0 and 1 already connected | |
| (5, 1, 3) | reject | |
| (6, 3, 4) | accept, 5 edges = n - 1, stop | {0,...,5} |

MST weight: 1 + 2 + 2 + 3 + 6 = 14. The edge (7, 3, 5) is never examined because the loop stops at n - 1 edges.

</details>

**11.7 ★★ Shortest paths in a DAG.** Write `dag_shortest_paths(graph, source)` that runs in O(V + E) on a weighted DAG, including one with negative edge weights. Explain why negative weights are safe here but not in Dijkstra.

<details>
<summary>Hint</summary>

If you process vertices in topological order, by the time you reach u, every edge into u has already been relaxed.

</details>

<details>
<summary>Solution</summary>

```python
def dag_shortest_paths(graph, source):
    """graph[u] is a list of (v, weight); the graph must be a DAG."""
    # Topological order by reverse DFS postorder (11.6).
    visited, postorder = set(), []

    def visit(u):
        visited.add(u)
        for v, _ in graph[u]:
            if v not in visited:
                visit(v)
        postorder.append(u)

    for u in graph:
        if u not in visited:
            visit(u)

    dist = {u: float('inf') for u in graph}
    dist[source] = 0
    for u in reversed(postorder):
        if dist[u] == float('inf'):
            continue                     # not reachable from source
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist
```

Every path into u consists of edges from vertices that come before u in topological order. All of those were processed, and their edges relaxed, before u, so `dist[u]` is final when u is processed, regardless of sign. There is no "greedy" step that assumes later edges can't help, which is exactly the assumption negative weights break in Dijkstra. Each vertex and edge is touched a constant number of times, so it is O(V + E).

Replacing each weight with its negation and running this gives the **longest** path in a DAG, which is the critical-path computation in project scheduling. (Longest path in a general graph is NP-hard.)

</details>

**11.8 ★★★ Word ladder.** Given a start word, a target word and a dictionary of equal-length words, find the minimum number of single-letter changes to turn start into target, where every intermediate word is in the dictionary (for example, COLD → CORD → CARD → WARD → WARM). The dictionary has N words of length L. Design an algorithm, state its complexity, and explain why building the graph explicitly by comparing all pairs is a poor idea.

<details>
<summary>Hint</summary>

The words are vertices, but you do not need the edges up front. Think about what all neighbours of "COLD" have in common.

</details>

<details>
<summary>Solution</summary>

It is BFS on an implicit graph whose vertices are words, with an edge between words differing in one position. BFS is right because edges are unweighted and we want the fewest steps.

Comparing all pairs to build the edges costs O(N² L): for N = 100,000 words that is 10^10 letter comparisons before the search even starts. Instead, bucket words by **wildcard patterns**: COLD belongs to the buckets `*OLD`, `C*LD`, `CO*D`, `COL*`. Two words are neighbours exactly when they share a bucket.

```python
from collections import defaultdict, deque

def ladder_length(start, target, words):
    buckets = defaultdict(list)
    for w in set(words) | {start}:
        for i in range(len(w)):
            buckets[w[:i] + '*' + w[i + 1:]].append(w)

    dist = {start: 0}
    queue = deque([start])
    while queue:
        w = queue.popleft()
        if w == target:
            return dist[w]
        for i in range(len(w)):
            key = w[:i] + '*' + w[i + 1:]
            for nxt in buckets[key]:
                if nxt not in dist:
                    dist[nxt] = dist[w] + 1
                    queue.append(nxt)
            buckets[key] = []            # each bucket only needs expanding once
    return None
```

Building the buckets costs O(N L²) (N words × L patterns × O(L) to build each pattern string). Clearing a bucket after its first expansion means each bucket's contents are scanned once in total, so the BFS is also O(N L²) overall. For the COLD → WARM example, it returns 4.

A further constant-factor improvement is **bidirectional BFS**: search from both ends and stop when the frontiers meet. If each word has about b neighbours and the answer is d steps, this explores roughly 2 b^(d/2) words instead of b^d.

</details>

---

## Where this connects

- [Chapter 5: Stacks and Queues](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md). The two containers that turn into DFS and BFS
- [Chapter 9: Heaps and Priority Queues](../volume-1/ch09-heaps-and-priority-queues.md). The structure inside Dijkstra and Prim, and why decrease-key matters
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The greedy and DP paradigms behind these algorithms
- [Chapter 23: Advanced Competitive Programming Data Structures](../volume-4/ch23-advanced-competitive-programming-data-structures.md). Heavy-light decomposition, link-cut trees and DSU with rollback, for graphs that change or are queried along paths
- [Chapter 28: Network Topology and Routing Data Structures](../volume-5/ch28-network-topology-and-routing-data-structures.md). The same graph structures applied to network routing
