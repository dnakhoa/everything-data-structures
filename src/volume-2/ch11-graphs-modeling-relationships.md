# Chapter 11: Graphs—Modeling Relationships

## 11.1 Graph Fundamentals

A graph G = (V, E) consists of:
- V: A set of vertices (also called nodes)
- E: A set of edges connecting pairs of vertices

```
Graph Example:
V = {A, B, C, D, E}
E = {(A,B), (A,C), (B,D), (C,D), (D,E)}

    A
   /│\
  / │ \
 B   C───D───E
```

## 11.2 Graph Types

**Directed vs. Undirected:**
- Undirected: Edges have no direction (relationships are symmetric)
- Directed: Edges have direction (A → B ≠ B → A)

**Weighted vs. Unweighted:**
- Weighted: Edges have weights (distances, costs)
- Unweighted: All edges equal weight 1

**Simple vs. Multi:**
- Simple: No loops, no parallel edges
- Multi: Parallel edges allowed

**Cyclic vs. Acyclic:**
- Cyclic: Contains cycles
- Acyclic: No cycles (DAGs if directed)

## 11.3 Graph Representations

### Adjacency Matrix

A V×V matrix where matrix[i][j] indicates edge presence:

```c
// For weighted graph
int adj[V][V];
// adj[i][j] = weight if edge exists, INF otherwise
```

```
Undirected Graph:
     A  B  C  D
   ┌──────────────
 A │ 0  1  1  0
 B │ 1  0  0  1
 C │ 1  0  0  1
 D │ 0  1  1  0

Space: O(V²)
```

**Pros**: O(1) edge queries, simple
**Cons**: O(V²) space even for sparse graphs

### Adjacency List

Store neighbors in linked lists or arrays:

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

**Pros**: O(V + E) space, good for sparse graphs
**Cons**: Edge lookup is O(degree)

## 11.4 Graph Traversal

### Breadth-First Search (BFS)

BFS explores vertices in order of distance from source:

```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])

    while queue:
        vertex = queue.popleft()
        print(vertex)

        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

Properties:
- Uses queue (FIFO)
- Produces shortest path in unweighted graphs
- Time: O(V + E)
- Space: O(V)

### Depth-First Search (DFS)

DFS explores deeply before backtracking:

```python
def dfs_recursive(graph, vertex, visited=None):
    if visited is None:
        visited = set()

    visited.add(vertex)
    print(vertex)

    for neighbor in graph[vertex]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)

def dfs_iterative(graph, start):
    visited = set()
    stack = [start]

    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            print(vertex)
            stack.extend(graph[vertex])
```

Properties:
- Uses stack (LIFO) or recursion
- Produces discovery/exploration order
- Time: O(V + E)
- Space: O(V)

## 11.5 Topological Sort

Topological sort orders vertices of a DAG so all edges go forward:

```python
def topological_sort(graph):
    in_degree = {v: 0 for v in graph}
    for v in graph:
        for u in graph[v]:
            in_degree[u] += 1

    queue = [v for v in graph if in_degree[v] == 0]
    result = []

    while queue:
        v = queue.pop(0)
        result.append(v)
        for u in graph[v]:
            in_degree[u] -= 1
            if in_degree[u] == 0:
                queue.append(u)

    return result
```

Applications:
- Build systems (make)
- Course scheduling
- Task dependencies
- Assembly instructions

## 11.6 Minimum Spanning Trees

A spanning tree connects all vertices with minimum total edge weight.

### Kruskal's Algorithm

Greedy edge-by-edge:

```python
def kruskal(graph):
    edges = sorted(graph.edges, key=lambda e: e.weight)
    uf = UnionFind(V)
    mst = []

    for edge in edges:
        u, v = edge.u, edge.v
        if uf.find(u) != uf.find(v):
            uf.union(u, v)
            mst.append(edge)
            if len(mst) == V - 1:
                break

    return mst
```

Time: O(E log E) or O(E log V)

### Prim's Algorithm

Grow MST from a vertex:

```python
def prim(graph, start):
    visited = {start}
    edges = []
    heap = [(w, start, v) for v, w in graph[start]]
    heapq.heapify(heap)

    while heap and len(visited) < len(graph):
        w, u, v = heapq.heappop(heap)
        if v in visited:
            continue

        visited.add(v)
        edges.append((u, v, w))

        for w2, v2 in graph[v]:
            if v2 not in visited:
                heapq.heappush(heap, (w2, v, v2))

    return edges
```

Time: O(E log V) with binary heap

## 11.7 Shortest Paths

### Single-Source: Dijkstra's Algorithm

For non-negative weights:

```python
import heapq

def dijkstra(graph, source):
    dist = {v: float('inf') for v in graph}
    dist[source] = 0
    pq = [(0, source)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue

        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))

    return dist
```

Time: O((V + E) log V)

### All-Pairs: Floyd-Warshall

Dynamic programming for all pairs:

```python
def floyd_warshall(graph):
    n = len(graph)
    dist = [[float('inf')] * n for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0
    for u in range(n):
        for v, w in graph[u]:
            dist[u][v] = w

    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist
```

Time: O(V³), Space: O(V²)

## 11.8 Union-Find (Disjoint Set Union)

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False

        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True
```

Time: O(α(n)) amortized (inverse Ackermann, effectively constant)

## 11.9 Applications

**Social Networks**: Friend suggestions, degrees of separation
**GPS/Maps**: Shortest routes, point-to-point navigation
**Internet**: Routing protocols (link-state, distance-vector)
**Web**: PageRank, web crawling
**Biology**: Protein interaction networks, evolutionary trees
**Finance**: Transaction graphs, fraud detection
**Recommendation Systems**: Collaborative filtering
