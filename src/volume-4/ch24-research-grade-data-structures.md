# Chapter 24: Research-Grade Data Structures

## 24.1 Introduction to Research-Grade Structures

Research-grade data structures push the boundaries of what is theoretically possible. They achieve remarkable space-time tradeoffs, often approaching information-theoretic lower bounds. These structures are essential for large-scale systems, specialized applications, and pushing the frontier of computer science.

## 24.2 Succinct Data Structures

### Conceptual Foundation

Succinct data structures store information in space close to the theoretical minimum while supporting efficient operations. They achieve entropy-compressed space.

**Space Bounds** (Z = the information-theoretic minimum number of bits for the object):
- **Implicit:** Z + O(1) bits
- **Succinct:** Z + o(Z) bits
- **Compact:** O(Z) bits
- **Compressed:** close to the data's empirical entropy (e.g. n·H₀ + o(n) bits), which can be well below Z

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
        before = self.rank_block[block - 1] if block > 0 else 0
        return before + sum(self.bits[block * 64: i + 1])

    def select(self, k):
        """Position of the k-th 1 (k counts from 0)"""
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
    depth = 1
    while depth > 0:
        i += 1
        depth += 1 if bp[i] == '(' else -1
    return i

def find_open(bp, i):
    """Find matching '(' for ')' at i"""
    depth = 1
    while depth > 0:
        i -= 1
        depth += 1 if bp[i] == ')' else -1
    return i
```

### LOUDS (Level-Order Unary Degree Sequence)

Level-order traversal with unary degree encoding. Each node: (degree times '(') + ')'.

| Operation | Complexity |
|-----------|------------|
| Root | O(1) |
| Parent | O(1) with O(1) rank/select |
| Children | O(d) |
| Subtree size | Not supported efficiently (use BP or DFUDS) |

## 24.4 Wavelet Matrices

### Conceptual Foundation

Wavelet matrices extend wavelet trees with better space utilization for large alphabets, using one bitmap per bit level with rank/select.

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
VEB Layout of a complete binary tree with h levels:
- If h = 1: single node
- If h > 1: cut the tree at half its height into a top tree
            of ceil(h/2) levels and about sqrt(N) bottom trees
            of floor(h/2) levels; lay out the top tree recursively,
            then each bottom tree recursively, left to right
```

**Search Complexity:** O(log_B N) I/Os, optimal.

## 24.7 External Memory Data Structures

### External Memory Model

Parameters: N (problem size), B (block size), M (memory size), and in the parallel disk model D (number of disks).

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
        self.node_id = node_id
        self.counts = {node_id: 0}

    def increment(self):
        self.counts[self.node_id] += 1

    def merge(self, other):
        for node, count in other.counts.items():
            self.counts[node] = max(self.counts.get(node, 0), count)

    def value(self):
        return sum(self.counts.values())
```

### Common CRDT Types

| CRDT | Operations | Semantics |
|------|------------|-----------|
| G-Set | Add | Grow-only |
| 2P-Set | Add, Remove | Remove-wins (no re-add) |
| LWW-Register | Assign | Last-write-wins |
| OR-Set | Add with tag, Remove | Tag-based |

## 24.10 Dynamic Graph Algorithms

### Holm-de Lichtenberg-Thorup (HDnT)

Fully dynamic connectivity with O(log² n) amortized updates and O(log n / log log n) queries:

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

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**24.1 ★ Rank and select by hand.** For the bit vector `1 0 1 1 0 0 1 0 1 1` (positions 0 to 9), compute `rank(i)` for every `i` using the definition in `SuccinctBitVector` (count of 1s in `[0, i]`), then `select(0)` and `select(3)`. How many calls to `rank` does the chapter's `select` make on a vector of n bits, and why is this class an illustration of rank/select rather than a succinct structure?

<details>
<summary>Solution</summary>

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| bit | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 0 | 1 | 1 |
| rank(i) | 1 | 1 | 2 | 3 | 3 | 3 | 4 | 4 | 5 | 6 |

`select(k)` (k counts from 0) is the smallest position whose rank exceeds k. `select(0) = 0` (first position with rank 1) and `select(3) = 6` (first position with rank 4). Rank and select are inverses in this sense: `rank(select(k)) = k + 1`.

The binary search in `select` halves `[0, n - 1]` each step, so it makes about ⌈log₂ n⌉ calls to `rank`, giving O(log n) select, not O(1).

It is not succinct, for two reasons. The bits are a Python list (one object per bit, not one bit per bit), and `rank_block` stores a full ⌈log₂ n⌉-bit count per 64 bits, which is Θ(n log n / 64) bits: a small constant for realistic n, but not o(n). And `rank` scans up to 64 list entries with `sum`, so it is O(64) work, not a word operation. A real succinct bit vector packs bits into machine words, uses a two-level directory (superblocks of about log² n bits, blocks of about ½ log n bits) so the directory totals o(n) bits, and finishes rank with a popcount instruction or lookup table, for O(1) time. Select needs its own o(n)-bit sampling directory to reach O(1).

</details>

**24.2 ★ 2P-Set versus OR-Set.** Two replicas start empty. Replica A runs `add(x)` then `remove(x)`. Concurrently, replica B runs `add(x)`. The replicas then merge. Afterwards, A runs `add(x)` again. Using the table in Section 24.9, say whether `x` is in the set after the merge and after the re-add, (a) for a 2P-Set and (b) for an OR-Set.

<details>
<summary>Solution</summary>

**(a) 2P-Set.** It is two G-Sets: `added` and `removed` (a tombstone set), and `x` is present iff it is in `added` and not in `removed`. Merge is union of both. After the merge, `added = {x}`, `removed = {x}`, so `x` is **absent**: B's concurrent add is overridden. A's re-add puts `x` into `added`, where it already is, and `x` is still in `removed` forever, so `x` stays **absent**. This is "remove-wins, no re-add".

**(b) OR-Set.** Each add creates a unique tag: A's add makes `(x, a1)`, B's makes `(x, b1)`. A remove deletes only the tags its replica has observed, so A's remove tombstones `a1` only. After the merge the live tags are `{b1}`, so `x` is **present**: the concurrent add wins. A's re-add creates `(x, a2)`, and `x` is **present**.

The difference is that the OR-Set remove says "remove the adds I have seen", which leaves concurrent adds alone, while the 2P-Set remove says "remove x", permanently.

</details>

**24.3 ★★ Balanced parentheses and LOUDS for the same tree.** Take the tree with root R, children A and B (in that order), where A has children C and D and B has child E. (a) Write its BP string (preorder, `(` on entry, `)` on exit). (b) Using `find_close`, compute the subtree sizes of R, A and B from their opening positions. (c) Write its LOUDS string following Section 24.3 (level order, each node writes `(` once per child, then `)`). (d) Explain why BP answers subtree size cheaply and LOUDS does not.

<details>
<summary>Hint</summary>

In BP, everything between a node's `(` and its matching `)` belongs to its subtree, and each node contributes exactly two characters.

</details>

<details>
<summary>Solution</summary>

(a) `R( A( C() D() ) B( E() ) )` gives

```
index: 0 1 2 3 4 5 6 7 8 9 10 11
bp:    ( ( ( ) ( ) ) ( ( )  )  )
node:  R A C   D     B E
```

so `bp = "((()())(()))"`, 2n = 12 characters for n = 6 nodes.

(b) Subtree size of the node opening at `i` is `(find_close(bp, i) - i + 1) / 2`:

- R at 0: `find_close = 11`, size `12 / 2 = 6`.
- A at 1: `find_close = 6`, size `6 / 2 = 3` (A, C, D).
- B at 7: `find_close = 10`, size `4 / 2 = 2` (B, E).

(c) Level order is R, A, B, C, D, E with degrees 2, 2, 1, 0, 0, 0:

```
R: (()   A: (()   B: ()   C: )   D: )   E: )
LOUDS = "(()(()())))"   (11 characters = (n − 1) opens + n closes)
```

Real implementations usually prepend one `(` for a virtual super-root so that every node, including the root, is "the child of someone", which makes the rank/select formulas uniform. That brings the length to 2n.

(d) In BP the subtree of a node is a contiguous substring, so its size is one `find_close` (O(1) with the standard o(n)-bit range-min directory). In LOUDS, a node's descendants are spread across every level below it, one contiguous run per level, so counting them means walking level by level. LOUDS is the better choice for fast parent and i-th child with the simplest directories; BP or DFUDS when you need subtree size, depth or level-ancestor.

</details>

**24.4 ★★ Why the G-Counter converges, and why you cannot just decrement it.** (a) Show that the `merge` of Section 24.9 is commutative, associative and idempotent, and explain why that guarantees all replicas converge no matter how often or in what order they exchange state. (b) A developer adds `def decrement(self): self.counts[self.node_id] -= 1`. Replica A increments three times, sends its state to B (B merges), then decrements once, then merges B's state back. What does A report, and what should it report? (c) How do you get a counter that supports decrement?

<details>
<summary>Hint</summary>

Merge is an entry-wise `max`. Think about what `max` does to a value that went down.

</details>

<details>
<summary>Solution</summary>

(a) Merge sets each entry to `max(mine, theirs)`. Entry-wise `max` is commutative (`max(a, b) = max(b, a)`), associative (`max(max(a, b), c) = max(a, max(b, c))`) and idempotent (`max(a, a) = a`). So the merged state after any set of exchanges is the entry-wise max over every state any replica has produced, regardless of order, grouping or duplicate deliveries. Once every replica has (directly or transitively) heard from every other, they all hold the same map, so `value()` agrees. This works because each entry only ever grows and only its owner writes it.

(b) After three increments A has `{A: 3}`; B merges and holds `{B: 0, A: 3}`. A decrements to `{A: 2}`. Merging B back computes `max(2, 3) = 3` for entry A. A reports **3**; the correct total is **2**. The decrement is silently lost, and whether it is lost depends on message timing, which is the bug CRDTs exist to prevent.

(c) Use a PN-Counter: two G-Counters, `P` for increments and `N` for decrements. `decrement` increments this replica's entry in `N`; merge merges `P` and `N` separately; the value is `sum(P) - sum(N)`. Every entry still only grows, so the convergence argument from (a) still holds.

</details>

**24.5 ★★ Lay out a tree in van Emde Boas order.** Number a complete binary tree with 4 levels in BFS order: root 1, children of `i` are `2i` and `2i + 1`, leaves 8 to 15. (a) Using the recursive rule in Section 24.6, write the 15 nodes in vEB order. (b) With blocks of B = 3 nodes, how many blocks does the root-to-leaf path 1, 2, 4, 8 touch in vEB order, and in plain BFS order? (c) Sketch why vEB order gives O(log_B N) blocks per search for every B at once.

<details>
<summary>Hint</summary>

With 4 levels, the top tree has 2 levels and there are four bottom trees of 2 levels each.

</details>

<details>
<summary>Solution</summary>

(a) Top tree: nodes 1, 2, 3 (itself laid out as 1, then 2, 3). Bottom trees, left to right: rooted at 4, 5, 6, 7, each with its two children.

```
vEB order: 1 2 3 | 4 8 9 | 5 10 11 | 6 12 13 | 7 14 15
```

(b) vEB, B = 3: positions split exactly as the bars above. Path 1, 2, 4, 8 sits in blocks `[1 2 3]` and `[4 8 9]`: **2 blocks**. BFS order stores node `i` at position `i − 1`, so the path is at positions 0, 1, 3, 7, which fall in blocks 0, 0, 1, 2: **3 blocks**. Every root-to-leaf path in this tree gives the same counts (2 versus 3). The gap grows with height: BFS order touches roughly one block per level once you are below the first log₂ B levels.

(c) Follow the recursion down until the pieces have between √B and B nodes. Each such piece is stored contiguously, so it straddles at most 2 blocks. A piece of at least √B nodes has height at least ½ log₂ B, so a root-to-leaf path of height log₂ N passes through at most `log₂ N / (½ log₂ B) = 2 log_B N` pieces, touching at most `4 log_B N` blocks. The argument never used the value of B in the layout itself, which is what "cache-oblivious" means: the same array is near-optimal for every level of the memory hierarchy.

</details>

**24.6 ★★ Read a fat node at a past time.** The `FatNode` of Section 24.8 logs every write as `(time, field, old, new)`, in increasing time order. Write `read(node, field, t)` that returns the value `node.<field>` had after all writes with time ≤ t. What is its cost, and which row of the persistence table does this node support?

<details>
<summary>Hint</summary>

You do not need to replay the log forward. Look for the first write to this field after time t.

</details>

<details>
<summary>Solution</summary>

The value at time t is the `old` value recorded by the first write to that field after t. If there is no such write, nothing has changed since t and the current attribute is the answer.

```python
def read(node, field, t):
    """Value of node.<field> as of time t (after every write with time <= t)."""
    for time, f, old, new in node.mod_log:
        if f == field and time > t:
            return old          # value just before the first later write
    return getattr(node, field) # no write after t: current value is the answer

n = FatNode(10)
n.write('value', 20, 1)
n.write('left', 'L', 2)
n.write('value', 30, 3)
n.write('value', 40, 5)
assert read(n, 'value', 0) == 10
assert read(n, 'value', 2) == 20
assert read(n, 'value', 4) == 30
assert read(n, 'value', 9) == 40
assert read(n, 'left', 1) is None and read(n, 'left', 2) == 'L'
```

This scan is O(m) for m logged writes. Keeping one log per field, each sorted by time, makes it a binary search: O(log m) per field access, so a root-to-leaf walk in a persistent tree of depth d costs O(d log m). That log factor is what the node-copying method (Driscoll, Sarnak, Sleator and Tarjan) removes.

`write` always appends at the current time and never branches from an old version, so this is **partial** persistence: read any version, write only the newest.

</details>

**24.7 ★★★ Count pattern occurrences with an FM-index.** (a) Compute `bwt("banana")` with the function in Section 24.5. (b) Build `C[c]` (number of characters in the text smaller than `c`) and use backward search to count occurrences of `"ana"` and of `"nab"`, keeping the suffix-array interval `[lo, hi)` at each step. (c) Implement `fm_count(L, pattern)` that does the same from the BWT string alone, without the original text.

<details>
<summary>Hint</summary>

Process the pattern from its last character. If the current interval of suffixes starting with `P[i+1:]` is `[lo, hi)`, then the suffixes starting with `c + P[i+1:]` form `[C[c] + occ(c, lo), C[c] + occ(c, hi))`, where `occ(c, i)` counts `c` in `L[:i]`.

</details>

<details>
<summary>Solution</summary>

(a) The sorted suffixes of `"banana$"` and the character before each:

| row | suffix | SA | L (preceding char) |
|-----|--------|----|----|
| 0 | `$` | 6 | a |
| 1 | `a$` | 5 | n |
| 2 | `ana$` | 3 | n |
| 3 | `anana$` | 1 | b |
| 4 | `banana$` | 0 | $ |
| 5 | `na$` | 4 | a |
| 6 | `nana$` | 2 | a |

`bwt("banana")` returns `("annb$aa", [6, 5, 3, 1, 0, 4, 2])`.

(b) The first column is `$aaabnn`, so `C[$] = 0`, `C[a] = 1`, `C[b] = 4`, `C[n] = 5`.

Pattern `"ana"`, right to left, starting from `[0, 7)`:

| char | lo | hi | rows |
|------|----|----|------|
| a | 1 + occ(a, 0) = 1 | 1 + occ(a, 7) = 4 | `a$`, `ana$`, `anana$` |
| n | 5 + occ(n, 1) = 5 | 5 + occ(n, 4) = 7 | `na$`, `nana$` |
| a | 1 + occ(a, 5) = 2 | 1 + occ(a, 7) = 4 | `ana$`, `anana$` |

Count = `4 − 2 = 2`. The SA entries in rows 2 and 3 (3 and 1) are the positions; a real FM-index stores only a sample of SA and recovers the rest with LF steps.

Pattern `"nab"`: `b` gives `[4, 5)`; then `a` gives `[1 + occ(a, 4), 1 + occ(a, 5)) = [2, 2)`, empty, so the count is **0**.

(c)

```python
def fm_count(L, pattern):
    C, total = {}, 0
    for ch in sorted(set(L)):
        C[ch] = total
        total += L.count(ch)

    def occ(ch, i):
        return L[:i].count(ch)  # a real index answers this in O(1) or O(log sigma)

    lo, hi = 0, len(L)
    for ch in reversed(pattern):
        if ch not in C:
            return 0
        lo = C[ch] + occ(ch, lo)
        hi = C[ch] + occ(ch, hi)
        if lo >= hi:
            return 0
    return hi - lo

L, sa = bwt("banana")
assert L == "annb$aa"
assert fm_count(L, "ana") == 2
assert fm_count(L, "nab") == 0
assert fm_count(L, "a") == 3
```

Backward search needs only `C` and `occ`, never the text, which is why the FM-index is self-indexing. With `occ` answered by a rank structure over L (a wavelet tree or wavelet matrix for general alphabets, Section 24.4), counting costs O(m) rank queries for a pattern of length m, independent of the text length.

</details>

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). Where this research is heading next
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). The cache-oblivious model several of these depend on
