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

## 24.7 Integer Data Structures and the Predecessor Problem

### The Predecessor Problem on a Word RAM

Maintain a set S of n keys drawn from the universe U = {0, 1, ..., u − 1}, under insert and delete, and answer:

- **predecessor(x):** the largest key in S that is smaller than x;
- **successor(x):** the smallest key in S that is larger than x.

(Some texts use ≤ and ≥; the difference is one membership test.) This is what an ordered map does for `floor`, `ceiling` and iteration, what a priority queue does when it finds the next nonempty priority level, and what an IP router does when it finds which address range a destination falls into.

A balanced BST or B-tree answers these in O(log n), and in the **comparison model** that is optimal: an algorithm that learns about keys only by comparing them is a binary decision tree, a query has n + 1 possible answers, so some query needs ⌈log₂(n + 1)⌉ comparisons. Integer keys are not opaque, though. On a **word RAM** with w-bit words (u = 2^w, and w ≥ log₂ n so that a word can hold a pointer), arithmetic, shifts, bitwise operations and reading memory at a computed address each cost O(1), and the decision-tree argument says nothing about algorithms that use them. Radix sort and hashing already escape comparison bounds this way. Hashing alone does not solve predecessor, because a hash table answers "is x in S?" in O(1) but knows nothing about order. The structures in this section answer predecessor queries in O(log log u) = O(log w) time: the recursion depth for 64-bit keys is 6, whatever n is.

### van Emde Boas Trees

Peter van Emde Boas (1975) introduced this structure as a priority queue. Split a k-bit key x (u = 2^k) into a high half and a low half:

high(x) = x >> ⌊k/2⌋,  low(x) = x mod 2^⌊k/2⌋,  x = high(x) · 2^⌊k/2⌋ + low(x).

This cuts the universe into about √u **clusters** of about √u keys each: high(x) names x's cluster and low(x) is its position inside. A vEB tree V over a universe of size u holds:

- `clusters[h]`: a vEB tree over the √u-sized universe of low halves, holding low(x) for every key x in cluster h;
- `summary`: a vEB tree over the √u cluster numbers, holding h for every nonempty cluster;
- `min` and `max`. The minimum is stored **only** here, never in a cluster. The maximum is a cached copy: it is also stored in its cluster.

When k is odd there are 2^⌈k/2⌉ clusters of 2^⌊k/2⌋ keys, so the summary gets the larger half of the bits.

Keeping the minimum out of the clusters is what makes the time bound work. Inserting into an empty vEB tree is O(1): set `min = max = x` and stop, with no recursion. So when insert finds x's cluster empty, it makes one recursive call into the summary (to record that the cluster is now nonempty) and an O(1) insert into the empty cluster. When the cluster is already nonempty, the summary does not change and the one recursive call goes into the cluster. Successor has the same shape: if x's cluster holds something larger than low(x), which the cluster's cached `max` tells us in O(1), recurse into the cluster; otherwise recurse into the summary to find the next nonempty cluster and read its `min` in O(1). Either way the work is **one recursive call on a universe of size √u, plus O(1)**:

T(u) = T(√u) + O(1).

Substitute m = log₂ u, the number of key bits. Each call halves m, so S(m) = S(m/2) + O(1), which is O(log m). Hence T(u) = O(log log u), **worst case**, for insert, delete, member, successor and predecessor, and O(1) for min and max. For 64-bit keys the bit count goes 64, 32, 16, 8, 4, 2, 1: seven levels. Without the cached `min` and `max`, successor would sometimes need two recursive calls, and T(u) = 2T(√u) + O(1) solves to O(log u), no better than a balanced tree (Exercise 24.8).

```python
class VEB:
    """van Emde Boas tree over the universe {0, ..., 2**k - 1}."""

    def __init__(self, k):
        self.k = k
        self.min = None              # kept here only, never inside a cluster
        self.max = None              # cached copy; the max also lives in a cluster
        if k > 1:
            self.lo_bits = k // 2    # bits of low(x); clusters have universe 2**lo_bits
            self.clusters = {}       # high(x) -> VEB(lo_bits), nonempty clusters only
            self.summary = None      # VEB of nonempty cluster numbers, built on demand

    def high(self, x):
        return x >> self.lo_bits

    def low(self, x):
        return x & ((1 << self.lo_bits) - 1)

    def index(self, h, l):
        return (h << self.lo_bits) | l

    def member(self, x):
        if x == self.min or x == self.max:
            return True
        if self.k == 1 or self.min is None:
            return False
        c = self.clusters.get(self.high(x))
        return c is not None and c.member(self.low(x))

    def insert(self, x):
        if self.min is None:                     # empty: O(1), no recursion
            self.min = self.max = x
            return
        if x == self.min or x == self.max:       # already present
            return
        if x < self.min:
            x, self.min = self.min, x            # x becomes the min; push the old min down
        if self.k > 1:
            h, l = self.high(x), self.low(x)
            c = self.clusters.get(h)
            if c is None:                        # new cluster: record it in the summary
                c = self.clusters[h] = VEB(self.lo_bits)
                if self.summary is None:
                    self.summary = VEB(self.k - self.lo_bits)
                self.summary.insert(h)           # the one real recursive call
            c.insert(l)                          # O(1) if c was empty, else the real call
        if x > self.max:
            self.max = x

    def successor(self, x):
        """Smallest element greater than x, or None."""
        if self.min is not None and x < self.min:
            return self.min
        if self.k == 1:
            return 1 if x == 0 and self.max == 1 else None
        h, l = self.high(x), self.low(x)
        c = self.clusters.get(h)
        if c is not None and l < c.max:          # answer is in x's own cluster
            return self.index(h, c.successor(l))
        if self.summary is None:                 # only the min is stored, and x >= min
            return None
        nxt = self.summary.successor(h)          # else: the next nonempty cluster
        if nxt is None:
            return None
        return self.index(nxt, self.clusters[nxt].min)

    def delete(self, x):
        """Remove x, which must be present."""
        if self.min == self.max:                 # x is the only element
            self.min = self.max = None
            return
        if self.k == 1:
            self.min = self.max = 1 - x
            return
        if x == self.min:                        # promote the smallest clustered element
            h = self.summary.min
            x = self.min = self.index(h, self.clusters[h].min)
        h, l = self.high(x), self.low(x)
        c = self.clusters[h]
        c.delete(l)
        if c.min is None:                        # cluster emptied (that delete was O(1))
            del self.clusters[h]
            self.summary.delete(h)
            if self.summary.min is None:
                self.summary = None
        if x == self.max:
            if self.summary is None:
                self.max = self.min
            else:
                h = self.summary.max
                self.max = self.index(h, self.clusters[h].max)
```

Delete follows the same pattern. Deleting the min promotes the smallest clustered key (the min of the summary's min cluster, found in O(1)) to be the new min, and deletes that key from its cluster instead. If the cluster delete empties the cluster, it was O(1), because the cluster held one key; the one real recursive call then removes the cluster number from the summary. The base case k = 1 is a universe {0, 1} described entirely by `min` and `max`. Predecessor is not quite the mirror image of successor, because the minimum lives outside the clusters; Exercise 24.9 works it out.

The class was checked against a sorted Python list on random sequences of insert, delete, member and successor, for universes of 2 to 2^20 keys, comparing `min` and `max` after every operation.

**Space, and the hashing fix.** van Emde Boas's structure stores the clusters in an array with a slot for every possible cluster, empty or not. Its space satisfies S(u) = (√u + 1) · S(√u) + Θ(√u), which is Θ(u). For 32-bit keys that is billions of words to hold even a handful of keys; for 64-bit keys it cannot be built. The fix is the one the code above already uses: keep only the nonempty clusters, in a hash table keyed by cluster number (the `dict`), and create a summary only when the first cluster appears. An insert creates at most one new structure per level of recursion (the cluster it found empty), so the space is O(n log log u) words. On random keys the class above uses about 2.6, 3.6 and 4.6 structures per key for 16-, 32- and 64-bit universes (n = 1000): one more per doubling of the word size, as the bound predicts. The price is that the time bounds now rest on hashing: O(log log u) expected for queries, and expected amortized for updates (tables resize). Getting down to O(n) space takes one more idea, bucketing, which is exactly the step from x-fast to y-fast tries below.

**Worked example (u = 16).** Insert S = {2, 3, 9, 13, 14, 15} into `VEB(4)`. Every key splits into 2 high bits and 2 low bits, so there are four clusters of four keys.

<figure>
{{#include ../images/veb-tree.svg}}
<figcaption>A vEB tree for u = 16: the minimum 2 lives only at the top, the summary records which clusters are nonempty, and the empty cluster 1 costs nothing. The green steps are successor(9).</figcaption>
</figure>

| Structure | Holds | min | max |
|-----------|-------|-----|-----|
| V (u = 16) | 2 at the top, the other keys in clusters | 2 | 15 |
| summary (u = 4) | cluster numbers 0, 2, 3 | 0 | 3 |
| cluster 0 (u = 4) | low 3 (key 3) | 3 | 3 |
| cluster 1 | not stored | | |
| cluster 2 (u = 4) | low 1 (key 9) | 1 | 1 |
| cluster 3 (u = 4) | lows 1, 2, 3 (keys 13, 14, 15) | 1 | 3 |

Key 2 is not in cluster 0: it is V's min. The summary and cluster 3 are vEB trees over u = 4 with the same rule. The summary keeps 0 as its min and stores 2 and 3 one level down (both in its cluster 1, since 2 = 10₂ and 3 = 11₂); cluster 3 keeps 1 as its min and stores 2 and 3 one level down.

- `successor(9)`: 9 = 10 01₂, so h = 2 and l = 1. Cluster 2's max is 1, not larger than l, so nothing in cluster 2 follows 9. The summary is asked for `successor(2)` among the nonempty clusters {0, 2, 3} and answers 3. Cluster 3's min is 1, so the answer is 3 · 4 + 1 = **13**.
- `successor(4)`: h = 1, and cluster 1 does not exist. The summary's successor of 1 is 2, and cluster 2's min is 1, so the answer is 2 · 4 + 1 = **9**. The empty cluster was skipped without being looked at.

Inside the summary, each query recursed once more on a universe of size 2 (into the summary's cluster 1 for `successor(2)`, into the summary's own summary for `successor(1)`) and stopped: one call per halving of the key length.

The cache-oblivious layout of Section 24.6 carries van Emde Boas's name because it applies the same recursion to a tree's height instead of a key's bits.

### x-Fast Tries

Willard (1983) reached the same O(log log u) query time by a different route, and then fixed the space.

Think of the keys as root-to-leaf paths in a complete binary trie of depth w: the path of x spells out its bits, most significant first, and the node at depth ℓ on that path is x's ℓ-bit prefix, x >> (w − ℓ). An ordinary binary trie finds where x's path leaves the set of stored paths by walking down, O(w) steps. The x-fast trie instead keeps, for each depth ℓ = 0, ..., w, a **hash table of the ℓ-bit prefixes of the keys in S**. Presence is monotone: if x's ℓ-bit prefix is present, so is every shorter prefix. So the length of x's longest present prefix can be found by **binary search over ℓ**, one hash lookup per step: O(log w) = O(log log u).

The node p where x's path stops has one child (if it had both, the path would continue), and x would go into the missing one. If the missing child is on the right, every key below p is smaller than x and the largest of them is x's predecessor; if it is on the left, every key below p is larger and the smallest is x's successor. Willard stores a *descendant pointer* at each node with a missing child, pointing at exactly that leaf, and links the leaves into a sorted doubly linked list, so the other neighbour is one step away. The sketch below keeps the (min, max) of the keys below each node instead, which carries the same information:

```python
def build_xfast(keys, w):
    """levels[l] maps each l-bit prefix of a key to (min, max) of the keys below it."""
    levels = [{} for _ in range(w + 1)]
    for x in keys:
        for l in range(w + 1):
            p = x >> (w - l)
            lo, hi = levels[l].get(p, (x, x))
            levels[l][p] = (min(lo, x), max(hi, x))
    srt = sorted(keys)
    nxt = dict(zip(srt, srt[1:] + [None]))      # the leaves as a sorted linked list
    return levels, nxt

def xfast_successor(levels, nxt, w, x):
    """Smallest key greater than x, or None."""
    if not levels[0]:
        return None
    lo, hi = 0, w                 # invariant: the prefix of length lo is present
    while lo < hi:                # binary search for the longest present prefix
        mid = (lo + hi + 1) // 2
        if (x >> (w - mid)) in levels[mid]:
            lo = mid
        else:
            hi = mid - 1
    if lo == w:                   # x itself is a key
        return nxt[x]
    mn, mx = levels[lo][x >> (w - lo)]
    if (x >> (w - lo - 1)) & 1:   # x leaves this node to the right of all its keys
        return nxt[mx]
    return mn                     # x leaves to the left of all its keys
```

Example: w = 4 and S = {2, 9, 13} = {0010, 1001, 1101}.

| ℓ | prefixes present (min, max of the keys below) |
|---|---|
| 0 | ε (2, 13) |
| 1 | `0` (2, 2), `1` (9, 13) |
| 2 | `00` (2, 2), `10` (9, 9), `11` (13, 13) |
| 3 | `001`, `100`, `110` (one key each) |
| 4 | `0010`, `1001`, `1101` (the keys) |

`successor(11)`, with 11 = 1011: start with lo = 0, hi = 4. Probe ℓ = 2: `10` is present, so lo = 2. Probe ℓ = 3: `101` is absent, so hi = 2. Two lookups locate node `10`. The next bit of 11 is 1, so 11 branches off to the right of everything under `10`, whose max is 9: 9 is the predecessor, and the next leaf in the list, **13**, is the successor. The code was checked against a sorted list on random sets for w from 1 to 32.

Queries cost O(log w) hash lookups, expected. The cost is elsewhere: each key puts a prefix into each of the w + 1 tables, so the space is O(nw) = O(n log u) words, and an insert or delete must update w + 1 tables (and the min, max or descendant pointers along the path), which is O(w) = O(log u) expected.

### y-Fast Tries

The y-fast trie, in the same paper, removes the factor of w by **bucketing** (also called indirection). Split the sorted keys into buckets of between w/2 and 2w consecutive keys, store each bucket in a balanced BST, and give each bucket a **representative**: a value no larger than the bucket's smallest key and larger than every key in the previous bucket. Only the representatives go into an x-fast trie. That is Θ(n/w) representatives at O(w) words each, plus O(n) for the BSTs: **O(n) space**.

- **successor(x):** find the largest representative ≤ x in the x-fast trie, O(log w). Search that bucket's BST for the successor of x, O(log w), since the bucket has O(w) keys. If nothing in the bucket is larger, the answer is the smallest key of the next bucket. (If no representative is ≤ x, it is the smallest key of the first bucket.)
- **insert / delete:** find the bucket the same way and update its BST, O(log w). When a bucket grows past 2w keys, split it and insert a new representative; when it falls below w/2, merge it with a neighbour, splitting the result again if it holds more than 3w/2 keys, and delete a representative. Each restructuring costs O(w), but it leaves every bucket involved with between about 3w/4 and 3w/2 keys, at least w/4 updates away from either limit, so it happens at most once per Ω(w) updates. Updates cost **O(log w) = O(log log u) amortized expected**.

A representative is a boundary, not a key. Deleting the key equal to its bucket's representative leaves the representative where it is, so ordinary updates never touch the x-fast trie.

Example, w = 4 (buckets of 2 to 8 keys): S = {1, 2, 3, 5, 8, 9, 12, 13, 14} in buckets {1, 2, 3, 5}, {8, 9, 12}, {13, 14} with representatives 0, 8 and 13. `successor(10)`: the largest representative ≤ 10 is 8, and the bucket {8, 9, 12} gives **12**. `successor(12)`: same bucket, nothing larger than 12, so the answer is the first key of the next bucket, **13**. Deleting 8 leaves the bucket {9, 12} with 2 = w/2 keys and representative 8, and the x-fast trie does not change.

All queries in x-fast and y-fast tries are expected bounds because of the hash tables. With dynamic perfect hashing, lookups take O(1) worst case, which makes the queries worst-case O(log log u), while updates stay expected amortized.

### Fusion Trees and Lower Bounds

**Fusion trees** (Fredman and Willard, 1990) attack the other parameter. A fusion tree is a B-tree with fan-out B = w^(1/5). Seen as paths in the binary trie, the B keys of one node branch at fewer than B bit positions; keeping only those bits gives each key a short *sketch*, and all B sketches fit in one word. A constant number of multiplications, masks and subtractions compare a query's sketch against every sketch in the node at once, and one more constant-time step corrects for the bits the sketch throws away. Each node is searched in O(1), the height is log_B n = O(log n / log w), so a query takes **O(log_w n)** time, in O(n) space.

Fusion trees win when w is large relative to log n; vEB and y-fast tries win when w is small. Taking whichever is better gives O(min(log_w n, log w)), which is always O(√(log n)): if log w ≥ √(log n) then log_w n = log n / log w ≤ √(log n), and otherwise log w < √(log n). Fredman and Willard used fusion trees to sort n integers in o(n log n) time, beating the comparison bound.

**Lower bounds.** Is O(log log u) the end of the story? For static sets, Pătraşcu and Thorup (2006) gave the answer: for every combination of n, word size w and space, the optimal query time up to constant factors, as the minimum of four expressions (the first is the fusion-tree bound log_w n), with matching lower bounds in the cell-probe model (which bound every word-RAM algorithm too). The case most often quoted: for a polynomial universe (w = γ log₂ n for a constant γ > 1, so u = n^γ) and near-linear space (n · (log n)^O(1) words), the optimal query time is Θ(log w) = Θ(log log u), so van Emde Boas's bound cannot be improved there. In the same setting with n^(1+ε) words of space, Beame and Fich's structure answers in O(log w / log log w), and Pătraşcu and Thorup showed that this gap between near-linear and polynomial space is real. As a function of n alone, the best possible query time with polynomial space is Θ(√(log n / log log n)): Beame and Fich proved the lower bound, and Andersson and Thorup's exponential search trees match it dynamically, in linear space.

### In Practice

| Structure | Predecessor / successor | Insert / delete | Space (words) |
|-----------|-------------------------|-----------------|---------------|
| Sorted array | O(log n) worst | O(n) worst | n |
| Balanced BST, B-tree | O(log n) worst | O(log n) worst | O(n) |
| vEB tree, arrays | O(log log u) worst | O(log log u) worst | Θ(u) |
| vEB tree, hash tables | O(log log u) expected | O(log log u) expected amortized | O(n log log u) |
| x-fast trie | O(log log u) expected | O(log u) expected amortized | O(n log u) |
| y-fast trie | O(log log u) expected | O(log log u) expected amortized | O(n) |
| Fusion tree | O(log_w n) worst | static as described | O(n) |

Here w = log₂ u is the word size. Min and max are O(1) in a vEB tree.

On paper, O(log log u) = 6 for 64-bit keys against log₂ n ≈ 30 for a billion keys. In memory, the count of operations is the wrong measure. Each level of a hashed vEB tree or x-fast trie is a hash probe at an unpredictable address, which on a large set is a cache miss, and a y-fast query adds a walk down a BST of about 64 keys. A B-tree with 16 to 64 keys per node over 10⁹ keys is 5 to 8 levels deep, each level a few adjacent cache lines that are scanned quickly (Chapter 10); it also gives range scans by walking adjacent memory, works for any ordered key type, and is far simpler. The hashed structures also use more memory: about 39 hash entries per key for an x-fast trie on 10⁶ random 64-bit keys (Exercise 24.10). For a general-purpose ordered map, a well-tuned B-tree, or a sorted array for static data, usually matches or beats them.

They pay off in specific places:

- **Small or dense universes.** When u is small enough to spend u bits, the vEB idea becomes a hierarchy of bitmaps with fan-out w: each node is one word with a bit per child, and "next set bit" is a shift and a count-trailing-zeros instruction. With 64-bit words, 4 levels cover u = 2^24 in u(1 + 1/63) bits, with no hashing and no pointers. The Linux O(1) scheduler (kernel 2.6.0 until the Completely Fair Scheduler replaced it in 2.6.23) found the highest-priority nonempty run queue with a single-level version: a 140-bit bitmap of priority levels and a find-first-set instruction. Memory allocators and timer implementations use the same multi-level bitmap trick.
- **IP routing.** Longest-prefix match by binary search over prefix lengths, with one hash table per length (Waldvogel, Varghese, Turner and Plattner, 1997), is the x-fast trie's idea applied to routing tables.
- **Theory.** These structures are the basis of integer sorting and integer priority queues that beat comparison bounds, for example in Dijkstra's algorithm with integer edge weights.

## 24.8 External Memory Data Structures

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

## 24.9 Fully Persistent Data Structures

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

## 24.10 Conflict-Free Replicated Data Types (CRDTs)

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

## 24.11 Dynamic Graph Algorithms

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

## 24.12 String B-Trees

B-trees optimized for string keys:

| Operation | I/O Complexity |
|-----------|----------------|
| Search | O(log_B n) |
| Prefix search | O(log_B n + output) |
| Range search | O(log_B n + output/B) |

## 24.13 Fractional Cascading

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

## 24.14 Melding Data Structures

Combine data structures efficiently:

| Structure | Meld Complexity |
|-----------|----------------|
| Fibonacci heap | O(1) |
| Binomial heap | O(log n) |
| Leftist heap | O(log n) |
| Skew heap | O(log n) amortized |

## 24.15 Research Frontiers

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

**24.2 ★ 2P-Set versus OR-Set.** Two replicas start empty. Replica A runs `add(x)` then `remove(x)`. Concurrently, replica B runs `add(x)`. The replicas then merge. Afterwards, A runs `add(x)` again. Using the table in Section 24.10, say whether `x` is in the set after the merge and after the re-add, (a) for a 2P-Set and (b) for an OR-Set.

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

**24.4 ★★ Why the G-Counter converges, and why you cannot just decrement it.** (a) Show that the `merge` of Section 24.10 is commutative, associative and idempotent, and explain why that guarantees all replicas converge no matter how often or in what order they exchange state. (b) A developer adds `def decrement(self): self.counts[self.node_id] -= 1`. Replica A increments three times, sends its state to B (B merges), then decrements once, then merges B's state back. What does A report, and what should it report? (c) How do you get a counter that supports decrement?

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

**24.6 ★★ Read a fat node at a past time.** The `FatNode` of Section 24.9 logs every write as `(time, field, old, new)`, in increasing time order. Write `read(node, field, t)` that returns the value `node.<field>` had after all writes with time ≤ t. What is its cost, and which row of the persistence table does this node support?

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

**24.8 ★ The vEB recurrences.** (a) Solve T(u) = T(√u) + O(1) by substituting m = log₂ u, and count the levels of recursion for u = 2^32 and u = 2^64. (b) Suppose the clusters did not cache their max, so that `successor` first calls `successor` on x's cluster and, only if that returns `None`, calls `successor` on the summary. Write the recurrence for the worst case and solve it. (c) Show that the array-based version's space, S(u) = (√u + 1) · S(√u) + Θ(√u), is Θ(u). Take u = 2^(2^i) so that every square root is exact.

<details>
<summary>Solution</summary>

(a) Let S(m) = T(2^m). Since √(2^m) = 2^(m/2), the recurrence becomes S(m) = S(m/2) + c, which unrolls to c · log₂ m + S(1). So T(u) = O(log m) = O(log log u). For u = 2^32 the key lengths are 32, 16, 8, 4, 2, 1: six levels. For u = 2^64 there are seven.

(b) In the worst case both calls happen: the cluster call runs all the way down and finds nothing, then the summary call runs. T(u) = 2T(√u) + O(1), so S(m) = 2S(m/2) + c, which is Θ(m) (the recursion tree has m leaves). That is T(u) = Θ(log u), no better than a balanced BST. The same thing happens to insert if the min is also stored in its cluster: inserting into an empty cluster would then recurse, so a new cluster would cost a full call on the summary and another on the cluster. The cached max and the "min lives only at the top" rule are each what keep the work to one call per level.

(c) Lower bound: count the base structures (u = 2). L(u) = (√u + 1) · L(√u) ≥ √u · L(√u) with L(2) = 1, so for u = 2^(2^i), L(u) ≥ 2^(2^(i−1)) · 2^(2^(i−2)) ⋯ 2^1 = 2^(2^i − 1) = u/2. Upper bound: write the extra term as at most a√u and let s₀ = S(2). Claim S(u) ≤ cu − b with c = a + s₀ and b = c + a. The base case holds: 2c − b = 2a + 2s₀ − 2a − s₀ = s₀. For the inductive step,

S(u) ≤ (√u + 1)(c√u − b) + a√u = cu − b + (c + a − b)√u ≤ cu − b,

since c + a − b = 0. So S(u) = Θ(u).

</details>

**24.9 ★★ Predecessor is not a mirror image.** Write `predecessor(V, x)`, the largest element of the `VEB` tree V smaller than x, or `None`. A natural first attempt mirrors `successor`: swap `min` with `max`, `<` with `>`, and `successor` with `predecessor`. Run that mirror on the u = 16 example of Section 24.7 for x = 3, 4 and 14, explain what goes wrong, and fix it. What is the running time of the fixed version?

<details>
<summary>Hint</summary>

Where does each structure keep its minimum? Successor never needs to look for a smaller element, so it never notices.

</details>

<details>
<summary>Solution</summary>

The mirror image returns `None` for x = 3 (the answer is 2) and for x = 4 (the answer is 3), and for x = 14 it crashes with a `TypeError` instead of returning 13.

- x = 3: cluster 0 holds only low 3, so nothing smaller is in it; the summary has no nonempty cluster before 0; the mirror gives up. But V's min, 2, is in no cluster, so the clusters never mention it.
- x = 4: the summary is asked for its predecessor of 1. The summary's own min, cluster number 0, lives only at the summary's top, so the same bug one level down returns `None` instead of 0.
- x = 14: cluster 3 is asked for its predecessor of 2. Its min, 1, lives only at its top, its inner clusters hold 2 and 3, so the inner call returns `None` and `V.index(3, None)` fails.

The fix: when no earlier nonempty cluster exists, the answer is the structure's own min, if that is smaller than x.

```python
def predecessor(V, x):
    """Largest element less than x, or None."""
    if V.max is not None and x > V.max:
        return V.max
    if V.k == 1:
        return 0 if x == 1 and V.min == 0 else None
    h, l = V.high(x), V.low(x)
    c = V.clusters.get(h)
    if c is not None and l > c.min:              # answer is in x's own cluster
        return V.index(h, predecessor(c, l))
    prev = predecessor(V.summary, h) if V.summary is not None else None
    if prev is None:                             # no earlier cluster, but the min
        if V.min is not None and x > V.min:      # lives outside every cluster
            return V.min
        return None
    return V.index(prev, V.clusters[prev].max)

V = VEB(4)
for key in [2, 3, 9, 13, 14, 15]:
    V.insert(key)
assert [predecessor(V, x) for x in (2, 3, 4, 10, 14, 15)] == [None, 2, 3, 9, 13, 14]
```

The fix adds an O(1) test and no recursive call, so predecessor is still one call on a universe of size √u plus O(1) work: O(log log u). (Checked against a sorted list on random sets for universes up to 2^12.)

</details>

**24.10 ★★ x-fast and y-fast tries by hand.** (a) For w = 4 and S = {3, 4, 10, 12}, list the prefixes stored at each level of the x-fast trie and count the hash-table entries. (b) Find the successor and predecessor of 9 by binary search over prefix lengths. Which prefixes are probed? (c) Estimate the number of hash-table entries for n = 10⁶ random 64-bit keys in an x-fast trie, and in a y-fast trie whose buckets hold 64 keys on average.

<details>
<summary>Solution</summary>

(a) In binary, 3 = 0011, 4 = 0100, 10 = 1010, 12 = 1100.

| ℓ | prefixes |
|---|---|
| 0 | ε |
| 1 | `0`, `1` |
| 2 | `00`, `01`, `10`, `11` |
| 3 | `001`, `010`, `101`, `110` |
| 4 | `0011`, `0100`, `1010`, `1100` |

That is 1 + 2 + 4 + 4 + 4 = 15 entries, fewer than n(w + 1) = 20 because keys share prefixes near the root.

(b) 9 = 1001. Start with lo = 0, hi = 4. Probe ℓ = 2: `10` is present, lo = 2. Probe ℓ = 3: `100` is absent, hi = 2. The search stops at node `10` after two probes. Its only child is `101` (key 10), and the next bit of 9 is 0, so 9 branches off to the left of every key under `10`: the successor is that subtree's min, **10**, and the predecessor is the leaf before 10 in the linked list, **4**.

(c) Level ℓ holds at most min(2^ℓ, n) prefixes. For random keys, the levels down to about ℓ = 20 (2^20 ≈ 10⁶) are nearly full and the deeper ones hold nearly n prefixes each. The expected total is Σ over ℓ = 0..64 of 2^ℓ (1 − (1 − 2^−ℓ)^n) ≈ 39 million entries, about 39 per key. At a prefix plus two words per entry that is close to a kilobyte per key before any hash-table overhead.

The y-fast trie puts only the 10⁶ / 64 ≈ 15,600 representatives in its x-fast trie. The same sum with n = 15,625 gives about 0.7 million entries, plus 10⁶ BST nodes for the buckets: under two stored items per key. Dividing the x-fast trie's population by w is exactly what turns O(nw) space into O(n).

</details>

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). Where this research is heading next
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). The cache-oblivious model several of these depend on
