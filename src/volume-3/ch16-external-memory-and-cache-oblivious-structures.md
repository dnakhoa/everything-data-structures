# Chapter 16: External Memory and Cache-Oblivious Structures

## 16.1 The Memory Hierarchy

<figure>
{{#include ../images/memory-hierarchy.svg}}
<figcaption>The hierarchy at human scale. This is why the RAM model mispredicts real performance.</figcaption>
</figure>

Modern computers have multiple levels of memory:
- L1 cache: ~32KB, ~1ns
- L2 cache: ~256KB, ~4ns
- L3 cache: ~8MB, ~15ns
- Main memory: ~64GB, ~100ns
- SSD: ~100GB, ~100μs
- Hard disk: ~TB, ~10ms

Read that list again as ratios rather than absolutes. Main memory is roughly 100× slower than L1. A disk seek is roughly 10,000,000× slower. Every complexity result in this book so far has assumed the RAM model from [Chapter 1](../volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md), where any memory access costs the same O(1). Across a spread that wide, that assumption is not an approximation. It is simply false, and it produces wrong predictions about which structure is faster.

The classic demonstration: a linked list and an array with identical asymptotic complexity for traversal, O(n), differ by 10× or more in wall-clock time. The array walks contiguous cache lines and the hardware prefetcher predicts every access. The list chases pointers to arbitrary addresses, and each hop is a potential cache miss. Same O(n), different machines being used.

Two things matter and the RAM model captures neither:

- **Transfers are blocked.** Memory does not move one word at a time. It moves in cache lines (typically 64 bytes) or disk pages (typically 4KB). Reading one byte costs the same as reading the whole block it sits in.
- **Locality is free performance.** If a structure arranges the data an algorithm touches together so it arrives in the same block, the remaining accesses cost nothing.

The structures in this chapter are the ones designed under those two facts instead of in spite of them.

## 16.2 External Memory Model

The I/O model accounts for disk access:
- B: Block size (elements per block)
- M: Internal memory size
- D: Disk access time relative to memory

Goal: Minimize block transfers.

The external memory model (also called the I/O model or the Aggarwal–Vitter model, after its 1988 authors)replaces "count the operations" with "count the block transfers." Computation on data already in memory is free; only I/O counts. This sounds crude, and it predicts real performance remarkably well.

The model changes the answers, not just the constants:

| Problem | RAM model | External memory model |
|---------|-----------|----------------------|
| Scan n elements | O(n) | O(n/B) |
| Sort n elements | O(n log n) | O((n/B) · log_(M/B) (n/B)) |
| Search, B-tree | O(log n) | O(log_B n) |
| Search, binary search tree | O(log n) | O(log n), one I/O per level |
| Search, binary search on sorted array | O(log n) | O(log (n/B)) |

The last three rows are the whole argument for [B-trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md). A balanced BST and a B-tree are both O(log n) in the RAM model, so the RAM model says they are equivalent. In the I/O model the BST costs one transfer per level while the B-tree packs B keys into each transfer, giving log_B n instead of log₂ n. With B = 512, a billion keys take 30 I/Os in a BST and 4 in a B-tree. That is not a constant-factor difference in any practical sense. It is the difference between a usable database index and an unusable one.

**Sorting is the other headline result.** The optimal external sort is a multiway merge with fanout M/B, not the binary merge you would write in memory: read M/B blocks at a time, merge them, write out. Reducing the number of passes over the data is everything, because each pass is n/B transfers. This is why external merge sort in a database uses hundreds of runs at once rather than merging two at a time.

**Cache-aware vs. cache-oblivious.** A structure that takes B and M as tuning parameters is *cache-aware* (B-trees are the canonical example: you pick the node size to match the page size). This works, but it must be re-tuned per machine, and it can only be tuned for one level of a hierarchy that has five. Tune your B-tree node to the disk page and you have said nothing about L1, L2, or L3.

## 16.3 Cache-Oblivious Structures

Cache-oblivious structures perform well at all cache levels without tuning:

**van Emde Boas Layout:**
```
Recursively divide at mid-level:

       ┌───────────────┐
       │       ○       │
       ├───────┬───────┤
       │   ○   │   ○   │
       ├───┬───┼───┬───┤
       │ ○ │ ○ │ ○ │ ○ │
       └───┴───┴───┴───┘
```

A cache-oblivious structure achieves the optimal I/O bound **without knowing B or M**. This sounds impossible (how do you optimize for a block size you were never told?)and the resolution is elegant: build the structure so that it is simultaneously well-organized at *every* scale. Whatever B turns out to be, some level of the recursion matches it.

The **van Emde Boas layout** is the foundational trick. Take a complete binary tree of height h and cut it horizontally at the middle, producing a top subtree of height h/2 and roughly √n bottom subtrees of height h/2. Lay each of those out recursively, and store them contiguously.

```
Tree:              Layout in memory:
      1            [1 | 2 4 5 | 3 6 7]
     / \            ↑     ↑       ↑
    2   3          top   sub1    sub2   ← each recursively vEB-laid-out
   /|   |\
  4 5   6 7
```

Now consider a root-to-leaf search under *any* block size B. Somewhere in the recursion there is a level whose subtrees have size between √B and B: those subtrees fit in one block. The search path crosses O(log_B n) such subtrees, so it costs O(log_B n) transfers. That is the same bound a B-tree achieves, obtained without ever naming B. And because the argument holds for every B simultaneously, the same layout is optimal for L1, L2, L3, RAM, and disk at once, which no cache-aware structure can be.

Compare the layouts directly:

| Layout | Search cost in I/Os | Needs tuning? |
|--------|--------------------|--------------|
| Sorted array + binary search | O(log(n/B)) | No, but poor locality at the top |
| Level-order (BFS) binary tree | O(log n) | No, worst of both |
| B-tree | O(log_B n) | Yes, node size = B |
| van Emde Boas layout | O(log_B n) | No |

The level-order row is worth noting because it is the layout most people write by default. Storing a binary tree breadth-first feels cache-friendly (it is contiguous, after all)but a root-to-leaf path in it touches one new block per level near the bottom, where almost all the nodes are.

**Other cache-oblivious results.** Funnelsort achieves the optimal sorting bound obliviously, using a recursively-defined merger structure. Cache-oblivious B-trees combine the vEB layout with a packed-memory array to support updates. These are theoretically beautiful and less common in production than the theory would suggest. The constant factors are worse than a well-tuned B-tree, and in practice you usually *do* know your page size.

## 16.4 What Production Systems Actually Do

<figure>
{{#include ../images/lsm-vs-btree.svg}}
<figcaption>The write path that separates B-trees from LSM trees.</figcaption>
</figure>

The ideas in this chapter show up in shipped code more often through their conclusions than their specific structures.

**B-trees everywhere.** Every relational database index, every filesystem (NTFS, HFS+, ext4, APFS all use B-trees or variants), and embedded stores like LMDB. Node size is matched to the page size.

**LSM trees** take the opposite approach to the same problem. Where a B-tree updates in place (costing a random write per update)a Log-Structured Merge tree buffers writes in a memory table, flushes them as sorted immutable runs, and merges runs in the background. Every disk write becomes sequential. Reads get slower (you may check several runs, which is what the Bloom filters from [Chapter 14](ch14-probabilistic-data-structures.md) mitigate) and space amplification goes up, but write throughput improves by an order of magnitude on both spinning disks and SSDs. This is the write-heavy tradeoff, and it is why LevelDB, RocksDB, Cassandra, and ScyllaDB use it.

**Column stores** (Parquet, ORC, ClickHouse) are external-memory thinking applied to analytics. A query touching 3 columns of a 200-column table reads 3/200ths of the blocks instead of all of them. Same asymptotics, ~60× fewer transfers.

**Struct-of-arrays** is the same reasoning at cache-line scale. Storing `{x[], y[], z[]}` rather than `{x,y,z}[]` means a loop over just the x values fills each cache line entirely with x values. Games and numerics rely on this heavily.

**Practical rules** that follow from the model:

1. Prefer contiguous layouts. `std::vector` beats `std::list` almost always, even when the asymptotics favor the list.
2. Match node sizes to blocks. A tree node should fill a cache line or a page, not straddle two.
3. Count passes over data, not operations. Two passes over 10GB is a real cost; the arithmetic in between usually is not.
4. Batch and sort. Random access converted into sequential access is often a 100× win.
5. Measure with hardware counters, not just a stopwatch. `perf stat` reports cache misses directly, which tells you whether you have a locality problem or a computation problem.

## 16.5 Historical Context

Alok Aggarwal and Jeffrey Vitter formalized the external memory model in their 1988 paper "The Input/Output Complexity of Sorting and Related Problems," establishing the sorting bound that still bears their names, though the practical wisdom substantially predates the theory, since Knuth's treatment of external sorting in *The Art of Computer Programming* Volume 3 (1973) covers tape-based merging in detail.

Cache-oblivious algorithms arrived much later. Harald Prokop's 1999 MIT master's thesis, supervised by Charles Leiserson, introduced the model and the van Emde Boas layout application, with the fuller treatment in Frigo, Leiserson, Prokop, and Ramachandran's FOCS 1999 paper. The layout itself is named for Peter van Emde Boas, who used the recursive halving idea in his 1975 priority queue: a structure solving an entirely different problem.

The LSM tree came from Patrick O'Neil and colleagues in 1996, and sat relatively unused until Google's Bigtable (2006) made it the default architecture for write-heavy distributed storage.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**16.1 ★ Count the I/Os.** An index holds n = 2³⁰ keys (about a billion) on disk, and a 4 KB page holds B = 256 keys. Using the table in Section 16.2, how many page reads does a lookup cost with (a) a balanced BST, one node per page; (b) binary search over a sorted array; (c) a B-tree with fanout 256? (d) How much memory would it take to cache the B-tree's top two levels, and how many reads does a lookup cost then?

<details>
<summary>Solution</summary>

(a) A balanced BST has height log₂ 2³⁰ = **30**, and each level is a separate page: 30 reads.

(b) Binary search narrows the range by half per probe, but once it is down to B keys the remaining probes stay in one page: about log₂(n/B) = log₂ 2²² = **22** reads.

(c) log₂₅₆ 2³⁰ = 30/8 = 3.75, so the tree has **4** levels (256³ = 2²⁴ keys is too few; 256⁴ = 2³² is enough): 4 reads.

(d) The top two levels are 1 + 256 = 257 pages, about **1 MB**. With them in memory, a lookup reads only the bottom two levels: **2** reads. This is why B-tree databases are fast in practice: the upper levels of every hot index sit in the buffer pool, and the cost of a lookup is one or two real I/Os. The same 257 pages would cache only the top 8 levels of the one-node-per-page BST (2⁸ − 1 = 255 pages), leaving 22 reads.

</details>

**16.2 ★★ External merge sort.** Sort N = 100 GB with M = 1 GB of memory and 1 MB blocks. (a) How many sorted runs does the first pass create? (b) How many merge passes does a multiway merge with fanout M/B need, and how many does a binary (two-way) merge need? (c) Compare the total data read and written. (d) Roughly how large could N be while still finishing in two passes?

<details>
<summary>Solution</summary>

(a) Read 1 GB at a time, sort it in memory, write it out: **100 runs** of 1 GB.

(b) Memory holds M/B = 1,000 one-block buffers. Keep one for output and the other 999 can each hold the current block of one run, so all 100 runs merge in **one pass**. A two-way merge halves the number of runs per pass: 100 → 50 → 25 → 13 → 7 → 4 → 2 → 1, which is ⌈log₂ 100⌉ = **7 passes**.

(c) Every pass reads and writes all 100 GB, so it moves 200 GB.

| Strategy | Passes (run formation + merges) | Data moved |
|----------|----------------------------------|------------|
| Multiway, fanout ~1,000 | 1 + 1 = 2 | 400 GB |
| Two-way | 1 + 7 = 8 | 1.6 TB |

At 500 MB/s of sequential throughput, that is about 13 minutes against about 53. The comparison counts are similar; the difference is entirely passes over the data, which is the point of the O((n/B) · log_(M/B)(n/B)) bound: here n/B = 100,000 blocks and log₁₀₀₀ 100,000 ≈ 1.7, so two passes.

(d) One merge pass can combine up to about 999 runs of 1 GB, so N up to roughly **1 TB** sorts in two passes. A third pass multiplies that by another ~1,000, to about 1 PB. With a reasonable amount of memory, external sorting almost never needs more than three passes.

</details>

**16.3 ★★ The van Emde Boas layout by hand.** Number a complete binary tree of height 4 in level order (root 1, children of i are 2i and 2i + 1, leaves 8 to 15). (a) Write out its van Emde Boas layout, cutting so the top tree has height 2. (b) Memory is read in aligned blocks of 3 nodes. How many blocks does the search path 1 → 2 → 5 → 11 touch in the vEB layout, and how many in the plain level-order layout 1, 2, ..., 15?

<details>
<summary>Solution</summary>

(a) The top tree is {1, 2, 3}. Below its leaves hang four bottom trees of height 2, rooted at 4, 5, 6 and 7, each stored as root then children:

```
[1 2 3 | 4 8 9 | 5 10 11 | 6 12 13 | 7 14 15]
```

(Each piece has height at most 2, so the recursion stops there.)

(b) With blocks of 3 the vEB layout splits exactly into those five pieces:

- vEB blocks: `[1 2 3] [4 8 9] [5 10 11] [6 12 13] [7 14 15]`. The path 1, 2, 5, 11 touches `[1 2 3]` and `[5 10 11]`: **2 blocks**.
- Level-order blocks: `[1 2 3] [4 5 6] [7 8 9] [10 11 12] [13 14 15]`. The path touches `[1 2 3]`, `[4 5 6]` and `[10 11 12]`: **3 blocks**.

Every root-to-leaf path costs 2 blocks in the vEB layout and 3 in level order. The difference is small at this size, but it is structural: in level order, the nodes on a path near the bottom are far apart because each level is twice as wide as the last, while the vEB layout keeps each small subtree, and therefore each short stretch of path, together.

</details>

**16.4 ★★ Predict the cache misses.** A 16384 × 16384 matrix of 8-byte doubles is stored row-major. A cache line holds 8 doubles, and the cache is an ideal fully associative LRU cache of 256 KB (4,096 lines). Count the misses for summing the matrix (a) row by row and (b) column by column. (c) Repeat (b) for a 2048 × 2048 matrix. What general rule does this show?

<details>
<summary>Hint</summary>

In (b), the next column wants the neighbouring double in each line you just loaded. Is that line still in the cache when you come back for it?

</details>

<details>
<summary>Solution</summary>

(a) Row by row reads memory sequentially. Each line is loaded once and all 8 doubles in it are used: n²/8 = 2²⁸/8 = 2²⁵ ≈ **33.6 million misses**.

(b) Walking down a column touches one double in each of 16,384 different lines (consecutive rows are 128 KB apart). The cache holds only 4,096 lines, so by the time the walk returns to the top for the next column, the line holding its neighbour was evicted long ago. Every access misses: n² = 2²⁸ ≈ **268 million misses**, 8 times as many as (a).

(c) A 2048 × 2048 column walk touches 2,048 lines, which fits in the 4,096-line cache. They survive until the next 7 columns reuse them, so the column-wise sum also costs only n²/8 = 2¹⁹ ≈ 0.5 million misses, the same as row-wise.

The rule: a traversal is cheap as long as its working set of blocks fits in memory, and falls off a cliff (here a factor of B = 8) the moment it does not. The RAM model sees both loop orders as identical O(n²). The I/O model predicts both the gap and where it starts. (Real caches are set-associative, and power-of-two strides map many rows to the same sets, so the cliff on actual hardware usually comes earlier than this ideal-cache count suggests. That is one more reason to traverse in storage order.)

</details>

**16.5 ★★ Design: B-tree or LSM tree?** Choose a storage engine for each workload and justify it. (a) An IoT platform ingesting 500,000 sensor readings per second, queried mostly as "the last hour of readings for device X". (b) A bank's account-balance table: small, frequent updates to existing rows, and point reads that must have predictable latency. (c) For workload (a), the per-run Bloom filters from Chapter 14 do almost nothing for the "last hour" query. Why?

<details>
<summary>Solution</summary>

(a) **LSM tree.** The workload is overwhelmingly writes, and an LSM tree turns every write into a sequential append to a memtable flush, where a B-tree would pay a random page write for each one. Reads are recent and keyed by (device, time), so they mostly hit the newest runs, which are small and likely cached. The price is background compaction (write amplification and I/O you do not directly control) and higher space amplification, both acceptable for append-mostly data.

(b) **B-tree.** Updates modify existing keys in place, and a point read is one root-to-leaf path, a predictable 1 to 2 I/Os with the upper levels cached. An LSM tree would leave several versions of hot accounts spread across runs until compaction, and a read may have to check several runs; compaction also introduces latency spikes. When predictable read latency matters more than write throughput, the B-tree's in-place update is the right trade.

(c) A Bloom filter answers "is this exact key in this run?". A range query asks "does this run hold *any* key between t₁ and t₂ for device X?", which a membership filter cannot answer without testing every possible key in the range. So a range scan must consult every run whose key range overlaps the query. What helps instead is each run's min/max key metadata (skip runs whose range does not overlap) and, if keys share a prefix such as the device ID, a filter built on that prefix rather than on the full key, which is what RocksDB's prefix Bloom filters do.

</details>

**16.6 ★★★ Measure the vEB layout.** Write `veb_order(height)`, returning the level-order node numbers of a complete binary tree in van Emde Boas order (give the top tree the smaller half of the height). Then, for a tree of height 20 (about a million nodes) and aligned blocks of B = 16, 64 and 512 nodes, find the worst-case number of blocks on any root-to-leaf path, for both the vEB layout and the level-order layout. Compare with log_B n and explain the results.

<details>
<summary>Hint</summary>

In level-order numbering, the leaves of a top tree of height t rooted at r are r · 2^(t−1) up to r · 2^(t−1) + 2^(t−1) − 1, and the bottom trees hang from their children. To find a path, walk up from a leaf with `node //= 2`.

</details>

<details>
<summary>Solution</summary>

```python
def veb_order(height, root=1):
    """Level-order numbers (root = 1, children 2i and 2i+1) of a complete
    binary tree of the given height, listed in van Emde Boas order."""
    if height == 1:
        return [root]
    top_h = height // 2                   # top gets the smaller half
    bottom_h = height - top_h
    order = veb_order(top_h, root)
    # The bottom subtrees hang below the top tree's leaves, left to right.
    first_leaf = root << (top_h - 1)
    for leaf in range(first_leaf, first_leaf + (1 << (top_h - 1))):
        for child in (2 * leaf, 2 * leaf + 1):
            order.extend(veb_order(bottom_h, child))
    return order

def blocks_on_path(position, leaf, block):
    """Distinct blocks touched by the root-to-leaf path ending at `leaf`."""
    seen = set()
    node = leaf
    while node >= 1:
        seen.add(position[node] // block)
        node //= 2
    return len(seen)

def worst_case(height, block, layout):
    if layout == "veb":
        order = veb_order(height)
    else:
        order = list(range(1, 2 ** height))   # level order
    position = {node: i for i, node in enumerate(order)}
    leaves = range(2 ** (height - 1), 2 ** height)
    return max(blocks_on_path(position, leaf, block) for leaf in leaves)

assert veb_order(3) == [1, 2, 4, 5, 3, 6, 7]
assert veb_order(4) == [1, 2, 3, 4, 8, 9, 5, 10, 11, 6, 12, 13, 7, 14, 15]
```

Running `worst_case(20, B, layout)` (a few seconds in CPython):

| B | log_B n (n ≈ 2²⁰) | vEB layout | Level order |
|---|-------------------|------------|-------------|
| 16 | 5.0 | 11 | 17 |
| 64 | 3.3 | 6 | 15 |
| 512 | 2.2 | 5 | 12 |

**Level order** costs h − log₂ B + 1 blocks: the top log₂ B levels share the first block, and then every level below costs a new block, because level d occupies 2^d consecutive slots and the path jumps further each time. That is Θ(log(n/B)), the same as binary search on a sorted array; for n much larger than B it is close to log₂ n, which is why Section 16.3's table lists it as O(log n). Larger blocks barely help it: going from B = 16 to B = 512 saves only 5 blocks.

**The vEB layout** tracks log_B n within a small constant factor, and it improves steadily as B grows, without the code ever being told B. The constant comes from the argument in Section 16.3: the path crosses subtrees whose height is between ½ log₂ B and log₂ B, so it crosses at most about 2 log_B n of them, and an unaligned subtree of at most B nodes can straddle 2 blocks. A B-tree with node size exactly B would do better on its one tuned level (5, 4 and 3 levels here), which is the practical case for B-trees made in Section 16.3: the oblivious layout is within a constant of optimal at every level of the hierarchy at once, but on any single level a tuned structure beats it.

</details>

---

## Where this connects

- [Chapter 10: Multiway Search Trees and B-Trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md). The B-trees this model exists to explain
- [Chapter 22: Practical Considerations](ch22-practical-considerations.md). Turning these findings into profiling decisions
