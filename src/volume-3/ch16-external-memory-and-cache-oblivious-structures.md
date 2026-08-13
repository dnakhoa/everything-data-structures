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

Read that list again as ratios rather than absolutes. Main memory is roughly 100× slower than L1. A disk seek is roughly 10,000,000× slower. Every complexity result in this book so far has assumed the RAM model from [Chapter 1](../volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md), where any memory access costs the same O(1). Across a spread that wide, that assumption is not an approximation — it is simply false, and it produces wrong predictions about which structure is faster.

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

The external memory model — also called the I/O model or the Aggarwal–Vitter model, after its 1988 authors — replaces "count the operations" with "count the block transfers." Computation on data already in memory is free; only I/O counts. This sounds crude, and it predicts real performance remarkably well.

The model changes the answers, not just the constants:

| Problem | RAM model | External memory model |
|---------|-----------|----------------------|
| Scan n elements | O(n) | O(n/B) |
| Sort n elements | O(n log n) | O((n/B) · log_(M/B) (n/B)) |
| Search, B-tree | O(log n) | O(log_B n) |
| Search, binary search tree | O(log n) | O(log n) — one I/O per level |
| Search, binary search on sorted array | O(log n) | O(log (n/B)) |

The last three rows are the whole argument for [B-trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md). A balanced BST and a B-tree are both O(log n) in the RAM model, so the RAM model says they are equivalent. In the I/O model the BST costs one transfer per level while the B-tree packs B keys into each transfer, giving log_B n instead of log₂ n. With B = 512, a billion keys take 30 I/Os in a BST and 4 in a B-tree. That is not a constant-factor difference in any practical sense — it is the difference between a usable database index and an unusable one.

**Sorting is the other headline result.** The optimal external sort is a multiway merge with fanout M/B, not the binary merge you would write in memory: read M/B blocks at a time, merge them, write out. Reducing the number of passes over the data is everything, because each pass is n/B transfers. This is why external merge sort in a database uses hundreds of runs at once rather than merging two at a time.

**Cache-aware vs. cache-oblivious.** A structure that takes B and M as tuning parameters is *cache-aware* (B-trees are the canonical example — you pick the node size to match the page size). This works, but it must be re-tuned per machine, and it can only be tuned for one level of a hierarchy that has five. Tune your B-tree node to the disk page and you have said nothing about L1, L2, or L3.

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

A cache-oblivious structure achieves the optimal I/O bound **without knowing B or M**. This sounds impossible — how do you optimize for a block size you were never told? — and the resolution is elegant: build the structure so that it is simultaneously well-organized at *every* scale. Whatever B turns out to be, some level of the recursion matches it.

The **van Emde Boas layout** is the foundational trick. Take a complete binary tree of height h and cut it horizontally at the middle, producing a top subtree of height h/2 and roughly √n bottom subtrees of height h/2. Lay each of those out recursively, and store them contiguously.

```
Tree:              Layout in memory:
      1            [1 | 2 3 | 4 5 | 6 7 ...]
     / \             ↑    ↑     ↑
    2   3          top  sub1  sub2   ← each recursively vEB-laid-out
   /|   |\
  4 5   6 7
```

Now consider a root-to-leaf search under *any* block size B. Somewhere in the recursion there is a level whose subtrees have size between √B and B — those subtrees fit in one block. The search path crosses O(log_B n) such subtrees, so it costs O(log_B n) transfers. That is the same bound a B-tree achieves, obtained without ever naming B. And because the argument holds for every B simultaneously, the same layout is optimal for L1, L2, L3, RAM, and disk at once — which no cache-aware structure can be.

Compare the layouts directly:

| Layout | Search cost in I/Os | Needs tuning? |
|--------|--------------------|--------------|
| Sorted array + binary search | O(log(n/B)) | No, but poor locality at the top |
| Level-order (BFS) binary tree | O(log n) | No — worst of both |
| B-tree | O(log_B n) | Yes, node size = B |
| van Emde Boas layout | O(log_B n) | No |

The level-order row is worth noting because it is the layout most people write by default. Storing a binary tree breadth-first feels cache-friendly — it is contiguous, after all — but a root-to-leaf path in it touches one new block per level near the bottom, where almost all the nodes are.

**Other cache-oblivious results.** Funnelsort achieves the optimal sorting bound obliviously, using a recursively-defined merger structure. Cache-oblivious B-trees combine the vEB layout with a packed-memory array to support updates. These are theoretically beautiful and less common in production than the theory would suggest — the constant factors are worse than a well-tuned B-tree, and in practice you usually *do* know your page size.

## 16.4 What Production Systems Actually Do

<figure>
{{#include ../images/lsm-vs-btree.svg}}
<figcaption>The write path that separates B-trees from LSM trees.</figcaption>
</figure>

The ideas in this chapter show up in shipped code more often through their conclusions than their specific structures.

**B-trees everywhere.** Every relational database index, every filesystem (NTFS, HFS+, ext4, APFS all use B-trees or variants), and embedded stores like LMDB. Node size is matched to the page size.

**LSM trees** take the opposite approach to the same problem. Where a B-tree updates in place — costing a random write per update — a Log-Structured Merge tree buffers writes in a memory table, flushes them as sorted immutable runs, and merges runs in the background. Every disk write becomes sequential. Reads get slower (you may check several runs, which is what the Bloom filters from [Chapter 14](ch14-probabilistic-data-structures.md) mitigate) and space amplification goes up, but write throughput improves by an order of magnitude on both spinning disks and SSDs. This is the write-heavy tradeoff, and it is why LevelDB, RocksDB, Cassandra, and ScyllaDB use it.

**Column stores** (Parquet, ORC, ClickHouse) are external-memory thinking applied to analytics. A query touching 3 columns of a 200-column table reads 3/200ths of the blocks instead of all of them. Same asymptotics, ~60× fewer transfers.

**Struct-of-arrays** is the same reasoning at cache-line scale. Storing `{x[], y[], z[]}` rather than `{x,y,z}[]` means a loop over just the x values fills each cache line entirely with x values. Games and numerics rely on this heavily.

**Practical rules** that follow from the model:

1. Prefer contiguous layouts. `std::vector` beats `std::list` almost always, even when the asymptotics favor the list.
2. Match node sizes to blocks. A tree node should fill a cache line or a page, not straddle two.
3. Count passes over data, not operations. Two passes over 10GB is a real cost; the arithmetic in between usually is not.
4. Batch and sort. Random access converted into sequential access is often a 100× win.
5. Measure with hardware counters, not just a stopwatch. `perf stat` reports cache misses directly, which tells you whether you have a locality problem or a computation problem.

## 16.5 Historical Context

Alok Aggarwal and Jeffrey Vitter formalized the external memory model in their 1988 paper "The Input/Output Complexity of Sorting and Related Problems," establishing the sorting bound that still bears their names — though the practical wisdom substantially predates the theory, since Knuth's treatment of external sorting in *The Art of Computer Programming* Volume 3 (1973) covers tape-based merging in detail.

Cache-oblivious algorithms arrived much later. Harald Prokop's 1999 MIT master's thesis, supervised by Charles Leiserson, introduced the model and the van Emde Boas layout application, with the fuller treatment in Frigo, Leiserson, Prokop, and Ramachandran's FOCS 1999 paper. The layout itself is named for Peter van Emde Boas, who used the recursive halving idea in his 1975 priority queue — a structure solving an entirely different problem.

The LSM tree came from Patrick O'Neil and colleagues in 1996, and sat relatively unused until Google's Bigtable (2006) made it the default architecture for write-heavy distributed storage.

---

## Where this connects

- [Chapter 10: Multiway Search Trees and B-Trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md) — the B-trees this model exists to explain
- [Chapter 22: Practical Considerations](ch22-practical-considerations.md) — turning these findings into profiling decisions
