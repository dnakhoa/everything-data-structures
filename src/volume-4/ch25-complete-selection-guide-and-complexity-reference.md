# Chapter 25: Complete Selection Guide and Complexity Reference

## 25.1 Data Structure Selection Matrix

| Need | Primary Choice | CP Alternative | Research Alternative |
|------|---------------|-----------------|----------------------|
| Range sum/query | Fenwick Tree | Segment Tree | Succinct Range Sum |
| Range min/max | Segment Tree | Sparse Table | Range Min Query |
| K-th order stat | Wavelet Tree | Merge Sort Tree | Wavelet Matrix |
| Path queries (tree) | HLD + SegTree | Link-Cut Tree | Euler Tour Tree |
| String search | Trie | Suffix Automaton | FM-Index |
| Palindromes | Palindromic Tree | Hash + binary | LCS-based |
| Dynamic connectivity | DSU (offline) | HDT (Holm–de Lichtenberg–Thorup) | Euler Tour Trees |
| Priority queue | Binary Heap | Fibonacci Heap | Buffered Heap |
| Ordered statistics | Order Statistic Tree | Treap | van Emde Boas |
| Approx membership | Bloom Filter | Cuckoo Filter | Quotient Filter |
| Approx counting | HyperLogLog | Count-Min Sketch | Count Sketch |

## 25.2 Complete Complexity Reference

### Competitive Programming Structures

| Structure | Build | Query | Update | Space |
|-----------|-------|-------|--------|-------|
| Segment Tree | O(n) | O(log n) | O(log n) | O(n) |
| Fenwick Tree | O(n) | O(log n) | O(log n) | O(n) |
| Heavy-Light Decomp | O(n) | O(log² n) | O(log² n) | O(n) |
| Link-Cut Tree | O(n) | O(log n) amortized | O(log n) amortized | O(n) |
| DSU with rollback | O(n) | O(log n) | O(log n) | O(n) |
| Mo's Algorithm | — | O(√n) amortized per query | — | O(n) |
| Sparse Table | O(n log n) | O(1) | Not supported | O(n log n) |
| Wavelet Tree | O(n log σ) | O(log σ) | Static | O(n log σ) |
| Suffix Automaton | O(n) | O(m) | Incremental | O(n), ≤ 2n−1 states |
| Palindromic Tree | O(n) | O(1) amortized | Incremental | O(n) |
| Li Chao Tree | O(n) | O(log C) | O(log C) | O(n) |

Two rows are easy to get wrong. **DSU with rollback is O(log n), not O(α(n))** — undoing a union requires knowing exactly which parent pointers changed, and path compression rewrites pointers all along the path, so rollback DSU must use union by rank alone. You trade the inverse-Ackermann bound for the ability to undo. And **Mo's algorithm is offline**: it answers q queries in O((n + q)√n) *total*, so the O(√n) is an amortized per-query share, not a bound on any individual query.

### Research-Grade Structures

| Structure | Space | Query | Notes |
|-----------|-------|-------|-------|
| Succinct Bit Vector | n + o(n) bits | O(1) rank and select | Optimal to within lower-order terms |
| FM-Index | n·H_k(T) + o(n log σ) bits | O(m) count | Self-indexing: replaces the text |
| LOUDS Tree | 2n + o(n) bits | O(1) navigation | Needs rank/select support |
| Wavelet Matrix | n log σ + o(n log σ) bits | O(log σ) | Faster constants than a wavelet tree |
| Cache-oblivious BST | O(n) | O(log_B n) I/Os | Optimal without knowing B |
| CRDT G-Counter | O(r) for r replicas | O(1) read, O(r) merge | Converges without coordination |
| Fibonacci Heap | O(n) | O(1) find-min, O(log n)★ delete-min | O(1) insert and O(1)★ decrease-key |
| HDT Dynamic Connectivity | O(n log n) | O(log n / log log n) | O(log² n)★ update (Holm–de&nbsp;Lichtenberg–Thorup) |

★ = amortized. **H_k(T)** is the k-th order empirical entropy of the text — the FM-index is compressed to the text's own entropy, which is what "self-indexing" means: you can discard the original text and still reconstruct any substring.

## 25.3 Algorithm Design Patterns

Each paradigm is defined by a bookkeeping question it must answer repeatedly, and becomes practical when a structure answers that question fast enough. [Chapter 21](../volume-3/ch21-algorithm-design-using-data-structures.md) develops this in full; the summary:

| Paradigm | Question asked repeatedly | Structure that answers it | Examples |
|----------|--------------------------|---------------------------|----------|
| Divide and conquer | Where do I resume? | Stack (implicit or explicit) | Quicksort, merge sort, binary search |
| Dynamic programming | Have I computed this state? | Array (dense) or hash map (sparse) | LCS, knapsack, edit distance |
| Greedy | What is the best remaining option? | Priority queue; union-find for connectivity | Huffman, Dijkstra, Prim, Kruskal |
| Backtracking | Can this branch still succeed, and how cheaply do I undo? | Bitmask, DLX, rollback DSU | N-Queens, Sudoku, exact cover |
| Randomized | (Defeat the adversary) | Depends — randomness *is* the technique | Quicksort, skip lists, treaps, Bloom filters |

The recurring trap: greedy is only correct when the problem has the matroid property or an equivalent exchange argument. Without it, greedy produces plausible wrong answers — which is worse than obviously wrong ones, because they pass casual testing.

---

## Where this connects

- [Chapter 22: Practical Considerations](../volume-3/ch22-practical-considerations.md) — the practical version of this decision process
