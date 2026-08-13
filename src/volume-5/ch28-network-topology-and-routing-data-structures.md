# Chapter 28: Network Topology and Routing Data Structures

## 28.1 Graph Representations for Networks

Network topology is fundamentally a graph problem. The choice of graph representation determines routing efficiency, memory usage, and update complexity.

### Adjacency Matrix vs Adjacency List

**Adjacency matrix** (O(V²) space):
```
  Router | A | B | C | D |
  -------|---|---|---|---|
     A   | 0 | 1 | 1 | 0 |
     B   | 1 | 0 | 0 | 1 |
     C   | 1 | 0 | 0 | 1 |
     D   | 0 | 1 | 1 | 0 |
```
- O(1) edge existence check
- O(V²) space even for sparse graphs
- Good for dense networks

**Adjacency list** (O(V + E) space):
```
A: B → 10, C → 5
B: A → 10, D → 3
C: A → 5, D → 7
D: B → 3, C → 7
```
- O(degree) neighbor enumeration
- Space proportional to actual edges
- Standard for network routing

### Compressed Representations for Large Networks

**CSR (Compressed Sparse Row)**: Store edges in three arrays:
- `offsets`: Starting position for each vertex's edges
- `edges`: Destination vertex IDs
- `weights`: Edge weights (optional)

**Routing tables** can use trie-like compression for hierarchical networks:
```
Hierarchical trie for routing:
           [root]
          /  |  \
        [A] [B] [C]
       /  \    /  \
    [A1][A2] [C1][C2]
```

## 28.2 Routing Table Structures

Routing tables map network prefixes to next hops. The data structure must support fast longest prefix match (LPM), the core operation of IP forwarding.

### Trie for Routing

Binary trie for IP addresses:
- Each level represents one bit
- 32 levels for IPv4, 128 for IPv6
- LPM: traverse bits until reaching longest matching prefix

**Memory explosion**: 2^32 possible leaves = 4 billion nodes. Solution: **compressed tries (Radix Tree / Patricia Tree)**.

### Radix Tree (Patricia Tree)

Collapse unary nodes (nodes with only one child) to reduce depth:

```
Standard trie path: 0→1→1→1→1
Radix tree: [01111] - single node representing this path

Example: 192.168.0.0/16, 192.168.1.0/24
    [192.168]
     /       \
  [0.0/16] [1.0/24]
```

**Linux routing cache** uses this structure internally. Memory per prefix: O(L) where L is number of bits until first branching.

### LC-Trie (Level Compressed Trie)

**Idea**: Group levels with low fan-out into arrays, apply trie compression to high-fan-out levels.

```
Level 0-7: Compressed into single node (2^7 prefix range)
Level 8-15: Second level compression
...
```

Used in **Cisco IOS** and many hardware routers. Enables hardware-accelerated lookup with minimal memory.

### Multi-bit Trie

Process multiple bits per step:
- 4-bit trie: Process 4 bits at a time (8 steps for IPv4 vs 32)
- 16-bit trie: Process 16 bits (2 steps for IPv4)

Trade-off: More memory (2^4 = 16 children per node) but faster lookup.

## 28.3 BGP Routing Data Structures

Border Gateway Protocol (BGP) routes between Autonomous Systems (AS). BGP routing tables are massive (~900K IPv4 prefixes as of 2024).

### BGPRIB (Routing Information Base)

BGP stores paths in a multi-attributed structure:
```
Prefix: 10.0.0.0/8
  └─ AS_PATH: [1239, 701, 80]
  └─ NEXT_HOP: 192.0.2.1
  └─ LOCAL_PREF: 100
  └─ MED: 50
  └─ ORIGIN: IGP
```

**Selection criteria** (in order):
1. Highest LOCAL_PREF
2. Shortest AS_PATH
3. Lowest ORIGIN (IGP < EGP < Incomplete)
4. Lowest MED
5. eBGP over iBGP
6. Lowest IGP metric to NEXT_HOP
7. Lowest router ID

### Path Vector Storage

AS_PATH is a sequence, not a set. Multiple paths to same destination create branching structures:

```
Dijkstra's algorithm adaptation for BGP:
- Priority queue ordered by path attributes
- Early exit when best path is known
- Incremental updates when AS_PATH changes
```

## 28.4 Software-Defined Networking (SDN) Tables

OpenFlow switch tables store flow entries with wildcard matching:

### TCAM (Ternary Content-Addressable Memory)

Hardware structure for wildcard matching:
- 0 = match bit exactly
- 1 = match bit exactly
- * = don't care (wildcard)

**Priority**: Longest match wins (evaluate in order).

```
Flow entry structure:
{
    match: {
        src_ip: 10.0.*.*,
        dst_ip: *.168.1.*,
        protocol: TCP,
        src_port: *,
        dst_port: 443
    },
    action: OUTPUT(port=3),
    priority: 100,
    stats: { packets: 1000, bytes: 50000 }
}
```

### Wildcard Compression

Multiple rules can be merged if they differ only on don't-care fields:
```
Rule 1: 10.0.0.0/8 with action A
Rule 2: 10.0.0.0/16 with action B
→ Cannot merge (Rule 2 is more specific)
```

## 28.5 Network Measurement Data Structures

### Count-Min Sketch

Estimate traffic flow frequencies:
```python
class CountMinSketch:
    def __init__(self, width, depth):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self.hash_functions = [generate_hash() for _ in range(depth)]

    def add(self, item, count=1):
        for i, h in enumerate(self.hash_functions):
            self.table[i][h(item) % self.width] += count

    def estimate(self, item):
        return min(
            self.table[i][h(item) % self.width]
            for i, h in enumerate(self.hash_functions)
        )
```

**Accuracy**: With width w and depth d, error ≤ ε·N with probability 1-δ where w = e/ε, d = ln(1/δ).

### Heavy Hitter Detection

Identify flows exceeding threshold T:
```python
class SpaceSaving:
    def __init__(self, k):
        self.k = k
        self.counters = {}  # flow_id -> count
        self.min_heap = []  # (count, flow_id) min-heap

    def add(self, item):
        if item in self.counters:
            self.counters[item] += 1
        elif len(self.counters) < self.k:
            self.counters[item] = 1
            heapq.heappush(self.min_heap, (1, item))
        else:
            # Evict minimum
            min_count, evict_item = heapq.heappop(self.min_heap)
            self.counters[evict_item] = 0
            self.counters[item] = min_count + 1
            heapq.heappush(self.min_heap, (min_count + 1, item))

    def top_k(self):
        return sorted(self.counters.items(), key=lambda x: -x[1])[:self.k]
```

## 28.6 Gossip Protocol Data Structures

Gossip-based systems use epidemic algorithms for dissemination. Each node periodically exchanges state with random peers.

### Anti-entropy

Periodic comparison and reconciliation:
```python
def anti_entropy(node, peer):
    # Exchange digests (summary of owned data)
    local_digest = node.compute_digest()
    remote_digest = peer.compute_digest()

    # Find differences
    differences = compare_digests(local_digest, remote_digest)

    # Synchronize
    for key, version in differences:
        if local_version < remote_version:
            node.request(key, peer)
        elif local_version > remote_version:
            peer.request(key, node)
```

**Convergence time**: O(log N) rounds for O(N log N) messages total.

### Broadcast Trees

Gossip can be organized into spanning trees for efficiency:
```
Root node creates spanning tree across cluster
Messages flow down tree (log N depth)
Negative acknowledgments flow up for reliability
```

**Swim protocol** for failure detection: Incremental membership updates with suspicion mechanism.

---

## Where this connects

- [Chapter 11: Graphs—Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md) — the graph fundamentals underneath routing
- [Chapter 13: String Data Structures](../volume-2/ch13-string-data-structures.md) — the tries that routing tables actually are
