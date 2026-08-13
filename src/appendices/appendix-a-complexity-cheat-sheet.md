# Appendix A: Complexity Cheat Sheet

Two conventions for reading these tables:

- **Average** assumes random or well-distributed data. **Worst** is the adversarial case. Where they differ, the gap is usually the whole story — a hash table is O(1) average and O(n) worst, and which one you get depends on your hash function and your adversary.
- ★ marks **amortized** bounds: cheap on average across a sequence of operations, with occasional expensive ones. A dynamic array append is O(1)★ because the resize that costs O(n) happens rarely enough to average out.

## A.1 Linear Structures

| Structure | Access by index | Search by value | Insert | Delete | Space |
|-----------|----------------|-----------------|--------|--------|-------|
| Static array | O(1) | O(n) | — | — | O(n) |
| Sorted array | O(1) | O(log n) | O(n) | O(n) | O(n) |
| Dynamic array | O(1) | O(n) | O(1)★ at end, O(n) elsewhere | O(n) | O(n) |
| Singly linked list | O(n) | O(n) | O(1) given the node | O(1) given the previous node | O(n) |
| Doubly linked list | O(n) | O(n) | O(1) given the node | O(1) given the node | O(n) |
| Stack | — | O(n) | O(1)★ | O(1)★ | O(n) |
| Queue | — | O(n) | O(1)★ | O(1)★ | O(n) |
| Deque | O(1) | O(n) | O(1)★ at either end | O(1)★ at either end | O(n) |

The linked-list rows come with the caveat that makes them much less useful than they look: insertion and deletion are O(1) **only once you already hold the relevant node**. Getting there is O(n), so an insert-at-position is O(n) overall.

## A.2 Trees and Ordered Maps

| Structure | Search (avg) | Search (worst) | Insert | Delete | Space |
|-----------|-------------|----------------|--------|--------|-------|
| BST (unbalanced) | O(log n) | O(n) | O(log n) / O(n) | O(log n) / O(n) | O(n) |
| AVL tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Red-black tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Splay tree | O(log n)★ | O(n) single op | O(log n)★ | O(log n)★ | O(n) |
| Treap | O(log n) expected | O(n) | O(log n) expected | O(log n) expected | O(n) |
| Skip list | O(log n) expected | O(n) | O(log n) expected | O(log n) expected | **O(n) expected** |
| B-tree / B+ tree | O(log_B n) I/Os | O(log_B n) I/Os | O(log_B n) | O(log_B n) | O(n) |
| Trie | O(L) | O(L) | O(L) | O(L) | O(N·A) |
| Radix / Patricia trie | O(L) | O(L) | O(L) | O(L) | O(N) |

Where **L** = key length, **N** = total characters stored across all keys, **A** = alphabet size.

Two rows worth reading carefully. **Skip list space is O(n) expected**, not O(n log n) — with promotion probability p = ½, the expected total number of nodes across all levels is 2n. The O(log n) is the expected *height*, which is a different quantity. And **splay trees** have no per-operation guarantee at all: a single access can cost O(n), and only a sequence of m operations is bounded, at O(m log n). That makes them unsuitable for latency-sensitive work regardless of their excellent amortized behavior.

## A.3 Hash-Based Structures

| Structure | Search (avg) | Search (worst) | Insert | Delete | Space |
|-----------|-------------|----------------|--------|--------|-------|
| Hash table (chaining) | O(1) | O(n) | O(1)★ | O(1) | O(n + m) |
| Hash table (open addressing) | O(1) | O(n) | O(1)★ | O(1) | O(m) |
| Cuckoo hashing | O(1) | **O(1) worst case** | O(1)★ expected | O(1) | O(n) |
| Perfect hashing (static) | O(1) | O(1) | — | — | O(n) |

Where **m** = number of buckets. Cuckoo hashing is the notable row: it is one of the few hash schemes with a genuine O(1) *worst-case* lookup, because a key can only live in one of two positions. Insertion pays for it, and can fail and require a full rehash.

Java's `HashMap` converts a bucket to a red-black tree past 8 entries, giving O(log n) rather than O(n) in the worst case — a defense against deliberate collision flooding.

## A.4 Heaps and Priority Queues

| Structure | Find min | Insert | Delete min | Decrease key | Merge | Space |
|-----------|----------|--------|-----------|--------------|-------|-------|
| Binary heap | O(1) | O(log n) | O(log n) | O(log n) | O(n) | O(n) |
| d-ary heap | O(1) | O(log_d n) | O(d·log_d n) | O(log_d n) | O(n) | O(n) |
| Binomial heap | O(log n) | O(1)★ | O(log n) | O(log n) | O(log n) | O(n) |
| Fibonacci heap | O(1) | O(1) | O(log n)★ | O(1)★ | O(1) | O(n) |
| Pairing heap | O(1) | O(1) | O(log n)★ | O(log log n)★ | O(1) | O(n) |

Building a heap from n existing elements is **O(n)**, not O(n log n) — Floyd's bottom-up heapify. This surprises people and is worth remembering.

Fibonacci heaps have the best bounds on this table and lose to binary heaps on most real workloads; see [Chapter 19](../volume-3/ch19-emerging-and-specialized-structures.md).

## A.5 Graphs

For a graph with V vertices and E edges:

| Operation | Adjacency list | Adjacency matrix |
|-----------|---------------|------------------|
| Space | O(V + E) | O(V²) |
| Add edge | O(1) | O(1) |
| Check edge (u,v) | O(deg(u)) | O(1) |
| Iterate neighbors of u | O(deg(u)) | O(V) |
| BFS / DFS | O(V + E) | O(V²) |

| Algorithm | Complexity | Requires |
|-----------|-----------|----------|
| BFS / DFS | O(V + E) | — |
| Topological sort | O(V + E) | DAG |
| Dijkstra (binary heap) | O((V + E) log V) | Non-negative weights |
| Dijkstra (Fibonacci heap) | O(E + V log V) | Non-negative weights |
| Bellman-Ford | O(V·E) | Detects negative cycles |
| Floyd-Warshall | O(V³) | All pairs |
| Kruskal MST | O(E log E) | Union-find |
| Prim MST (binary heap) | O(E log V) | — |
| Union-Find (path compression + union by rank) | O(α(n)) ★ | — |
| **Union-Find with rollback** | **O(log n)** | No path compression |

That last row is a common trap. Rollback requires undoing parent changes, which path compression makes impossible to track cheaply — so rollback DSU uses union by rank alone and costs O(log n), not O(α(n)).

α(n) is the inverse Ackermann function, below 5 for any n that fits in the observable universe.

## A.6 Probabilistic and Specialized

| Structure | Query | Insert | Space | Error |
|-----------|-------|--------|-------|-------|
| Bloom filter | O(k) | O(k) | ~1.44·log₂(1/ε)·n bits | False positives only |
| Counting Bloom filter | O(k) | O(k) | 4× a Bloom filter | False positives only |
| Cuckoo filter | O(1) | O(1)★ | ~(log₂(1/ε) + 3)·n bits | False positives; supports delete |
| HyperLogLog | O(1) | O(1) | O(log log n) — ~12KB for billions | ~2% cardinality error |
| Count-Min Sketch | O(k) | O(k) | O((1/ε)·log(1/δ)) | Overestimates only |
| Skip list | O(log n) expected | O(log n) expected | O(n) expected | None — exact |

A Bloom filter with 1% false-positive rate needs about 9.6 bits per element regardless of how large the elements are, which is the property that makes it useful.

## A.7 Competitive Programming Structures

| Structure | Build | Query | Update | Space |
|-----------|-------|-------|--------|-------|
| Prefix sum array | O(n) | O(1) | Rebuild O(n) | O(n) |
| Fenwick tree (BIT) | O(n) | O(log n) | O(log n) | O(n) |
| Segment tree | O(n) | O(log n) | O(log n) | O(n) |
| Segment tree + lazy propagation | O(n) | O(log n) | O(log n) range | O(n) |
| Sparse table | O(n log n) | O(1) | Not supported | O(n log n) |
| Sqrt decomposition | O(n) | O(√n) | O(1) | O(n) |
| Mo's algorithm | — | O(√n) ★ per query | — | O(n) |
| Heavy-light decomposition | O(n) | O(log² n) | O(log² n) | O(n) |
| Link-cut tree | O(n) | O(log n)★ | O(log n)★ | O(n) |
| Wavelet tree | O(n log σ) | O(log σ) | Static | O(n log σ) |
| Suffix array (SA-IS) | O(n) | O(m log n) | Static | O(n) |
| Suffix automaton | O(n) | O(m) | Incremental | O(n) — ≤ 2n−1 states |
| Suffix tree | O(n) | O(m) | Static | O(n) |
| Palindromic tree (eertree) | O(n) | O(1)★ | Incremental | O(n) |
| Li Chao tree | O(n) | O(log C) | O(log C) | O(n) |

Where **σ** = alphabet size, **m** = pattern length, **C** = coordinate range.

Mo's algorithm is offline and processes q queries in O((n + q)√n) *total*; the O(√n) figure is the amortized per-query share, not a bound on any single query.

## A.8 Complexity Growth Reference

How the classes actually behave, for intuition about when each becomes infeasible:

| n | O(log n) | O(n) | O(n log n) | O(n²) | O(2ⁿ) |
|---|---------|------|-----------|-------|-------|
| 10 | 3 | 10 | 33 | 100 | 1,024 |
| 100 | 7 | 100 | 664 | 10,000 | 10³⁰ |
| 1,000 | 10 | 1,000 | 9,966 | 10⁶ | — |
| 10⁶ | 20 | 10⁶ | 2×10⁷ | 10¹² | — |
| 10⁹ | 30 | 10⁹ | 3×10¹⁰ | 10¹⁸ | — |

Rough practical ceilings at roughly 10⁸ simple operations per second: O(n²) is fine to n ≈ 10,000; O(n log n) to n ≈ 10⁷; O(n) to n ≈ 10⁸; O(2ⁿ) to n ≈ 25; O(n!) to n ≈ 11.
