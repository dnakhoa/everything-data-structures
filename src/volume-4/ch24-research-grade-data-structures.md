# Chapter 24: Research-Grade Data Structures

## 24.1 Introduction to Research-Grade Structures

Research-grade data structures push the boundaries of what is theoretically possible. They achieve remarkable space-time tradeoffs, often approaching information-theoretic lower bounds. These structures are essential for large-scale systems, specialized applications, and pushing the frontier of computer science.

## 24.2 Succinct Data Structures

### Conceptual Foundation

Succinct data structures store information in space close to the theoretical minimum while supporting efficient operations. They achieve entropy-compressed space.

**Space Bounds:**
- **Succinct:** n·H₀ + O(n / log n) bits
- **Compact:** O(n log σ) bits
- **Implicit:** n + O(1) bits

### Rank and Select

```python
class SuccinctBitVector:
    def __init__(self, bits):
        self.bits = bits
        self.n = len(bits)
        self._build_rank()

    def _build_rank(self):
        self.rank_block = [0] * ((self.n + 63) // 64)
        for i in range(self.n):
            if self.bits[i]:
                self.rank_block[i // 64] += 1
        for i in range(1, len(self.rank_block)):
            self.rank_block[i] += self.rank_block[i - 1]

    def rank(self, i):
        """Count of 1s in [0, i]"""
        block = i // 64
        return self.rank_block[block] + bin(
            self.bits[block * 64: i + 1]
        ).count('1')

    def select(self, k):
        """Position of k-th 1"""
        lo, hi = 0, self.n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.rank(mid) <= k:
                lo = mid + 1
            else:
                hi = mid
        return lo
```

## 24.3 Succinct Trees (LOUDS, BP, DFUDS)

### Balanced Parentheses (BP)

Tree → balanced parentheses string where "(" means enter node, ")" means exit.

```python
def find_close(bp, i):
    """Find matching ')' for '(' at i"""
    delta = -1
    while delta < 0:
        i += 1
        delta += 1 if bp[i] == '(' else -1
    return i

def find_open(bp, i):
    """Find matching '(' for ')' at i"""
    delta = 1
    while delta > 0:
        i += 1
        delta += 1 if bp[i] == '(' else -1
    return i - 1
```

### LOUDS (Level-Order Unary Degree Sequence)

Level-order traversal with unary degree encoding. Each node: (degree times '(') + ')'.

| Operation | Complexity |
|-----------|------------|
| Root | O(1) |
| Parent | O(log n) |
| Children | O(d) |
| Subtree size | O(1) |

## 24.4 Wavelet Matrices

### Conceptual Foundation

Wavelet matrices extend wavelet trees with better space utilization and dynamic alphabet support using bitmaps with rank/select.

**Improvements over Wavelet Tree:**
- No separate child arrays
- Better bit-level packing
- Same query complexity

## 24.5 FM-Index

### Conceptual Foundation

The FM-Index (Ferragina-Manzini) is a compressed self-indexing text index using the Burrows-Wheeler Transform.

**Key Components:**
- BWT string
- Occurrence counts (compressed)
- Suffix array samples
- LF-mapping

```python
def bwt(s):
    """Burrows-Wheeler Transform"""
    s = s + '$'
    suffixes = sorted(range(len(s)), key=lambda i: s[i:])
    return ''.join(s[i-1] for i in suffixes), suffixes
```

## 24.6 Cache-Oblivious Data Structures

### Conceptual Foundation

Cache-oblivious structures achieve optimal performance without knowing cache size M or block size B. They work well across all memory hierarchy levels.

**Key Idea:** Optimal algorithms for all configurations simultaneously.

### van Emde Boas Layout

```
Tree layout recursively:
VEB Layout of tree with height h:
- If h = 0: single node
- If h > 0: layout of left subtree of size 2^(h-1),
            then layout of right subtree of size 2^(h-1)
```

**Search Complexity:** O(log_B N) I/Os, optimal.

## 24.7 External Memory Data Structures

### External Memory Model

Parameters: B (block size), M (memory size), D (disk latency).

| Structure | I/O Complexity |
|-----------|----------------|
| B-Tree | O(log_B N) |
| Buffer Tree | O(1/B log_M/B N) amortized |
| LSM Tree | O(1/B log_M/B N) amortized write |

### Log-Structured Merge Trees

LSM trees (LevelDB, RocksDB, Cassandra) achieve write-optimized storage:

```
Levels: L0, L1, L2, ..., L_k
- Each level T times larger than previous
- Data flows: MemTable → L0 → L1 → ... → Lk
- Compaction merges sorted runs
```

## 24.8 Fully Persistent Data Structures

### Persistence Types

| Type | Read Old | Write Current | Write Old | Merge |
|------|----------|---------------|-----------|-------|
| Partial | Yes | Yes | No | No |
| Full | Yes | Yes | Yes | No |
| Confluent | Yes | Yes | Yes | Yes |

### Fat Nodes

Store modification logs at each node:

```python
class FatNode:
    def __init__(self, value):
        self.value = value
        self.mod_log = []  # (time, field, old, new)
        self.left = None
        self.right = None

    def write(self, field, new_value, time):
        self.mod_log.append((time, field, getattr(self, field), new_value))
        setattr(self, field, new_value)
```

## 24.9 Conflict-Free Replicated Data Types (CRDTs)

### Conceptual Foundation

CRDTs achieve eventual consistency in distributed systems without coordination. Operations commute, guaranteeing convergence.

### G-Counter (Grow-only)

```python
class GCounter:
    def __init__(self, node_id):
        self.counts = {node_id: 0}

    def increment(self):
        self.counts[self.node_id] += 1

    def merge(self, other):
        for node, count in other.items():
            self.counts[node] = max(self.counts.get(node, 0), count)

    def value(self):
        return sum(self.counts.values())
```

### Common CRDT Types

| CRDT | Operations | Semantics |
|------|------------|-----------|
| G-Set | Add | Grow-only |
| 2P-Set | Add, Remove | Add-wins |
| LWW-Register | Assign | Last-write-wins |
| OR-Set | Add with tag, Remove | Tag-based |

## 24.10 Dynamic Graph Algorithms

### Holm-de Lichtenberg-Thorup (HDnT)

Fully dynamic connectivity in O(log n):

```python
class HDnTConnectivity:
    def __init__(self, n):
        self.n = n
        self.LOG = int(math.log2(n)) + 1
        self.levels = [[] for _ in range(self.LOG)]
        self.spanning_forests = [None] * self.LOG
```

### Dynamic Shortest Paths

| Type | Best Known |
|------|------------|
| Decremental APSP | O(mn) total |
| Fully dynamic | O(n²) per update |
| (1+ε)-approx | Near-linear |

## 24.11 String B-Trees

B-trees optimized for string keys:

| Operation | I/O Complexity |
|-----------|----------------|
| Search | O(log_B n) |
| Prefix search | O(log_B n + output) |
| Range search | O(log_B n + output/B) |

## 24.12 Fractional Cascading

Accelerate searches in layered structures:

```python
def fractional_cascading_search(layers, query):
    """Search in multiple layers with caching"""
    pos = binary_search(layers[0], query)
    for i in range(1, len(layers)):
        # Use cached bounds from previous level
        cached_lower = layers[i-1].get_cached_lower(pos)
        pos = bounded_search(layers[i], query, cached_lower)
    return pos
```

**Speedup:** O(log n + k) vs O(Σ log n_i)

## 24.13 Melding Data Structures

Combine data structures efficiently:

| Structure | Meld Complexity |
|-----------|----------------|
| Fibonacci heap | O(1) |
| Binomial heap | O(log n) |
| Leftist heap | O(log n) |
| Skew heap | O(log n) amortized |

## 24.14 Research Frontiers

### Emerging Areas

| Area | Challenge | State |
|------|-----------|-------|
| Succinct graphs | Space-time tradeoffs | O(n) space |
| Dynamic graph minors | Subgraph isomorphism | Active research |
| Learned indexes | Replace B-trees with neural nets | Emerging |
| Quantum DS | Quantum advantage | Theoretical |
| DNA storage | Extreme longevity | Nanostores |

### Open Problems

1. Dynamic connectivity in true O(log n)?
2. Sub-logarithmic string operations?
3. Persistent arrays with O(1) space per version?
4. Cache-oblivious sorting optimal?

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). Where this research is heading next
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). The cache-oblivious model several of these depend on
