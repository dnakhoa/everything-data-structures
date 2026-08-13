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
| Dynamic connectivity | DSU (offline) | HDnT | Euler Tour Trees |
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
| Link-Cut Tree | O(n) | O(log n) | O(log n) | O(n) |
| DSU Rollback | O(n α) | O(α) | O(α) | O(n) |
| Mo's Algorithm | O(n√n) | O(n√n) | - | O(n) |
| Sparse Table | O(n log n) | O(1) | - | O(n log n) |
| Wavelet Tree | O(n log σ) | O(log σ) | - | O(n log σ) |
| Suffix Automaton | O(n) | O(m) | - | O(2n) |
| Palindromic Tree | O(n) | O(log n) | - | O(n) |
| Li Chao Tree | - | O(log C) | O(log C) | O(n) |

### Research-Grade Structures

| Structure | Space | Query | Notes |
|-----------|-------|-------|-------|
| Succinct Bit Vector | n bits | O(1) rank | Optimal |
| FM-Index | n·H_k | O(m) | Compressed |
| LOUDS Tree | 2n bits | O(log n) | Simple |
| Wavelet Matrix | n log σ | O(log σ) | Dynamic α |
| Cache-oblivious BST | O(n) | O(log_B n) | Optimal I/O |
| CRDT G-Counter | O(n) | O(1) | Distributed |
| Fibonacci Heap | O(n) | O(log n) amort | O(1) insert |
| HDnT Connectivity | O(n log n) | O(log n) | Dynamic |

## 25.3 Algorithm Design Patterns

**Divide and Conquer:**
- Quicksort: Partition around pivot
- Merge sort: Divide at midpoint
- Binary search: Halve search space

**Dynamic Programming:**
- Memoization with hash table
- Tabulation with array

**Greedy:**
- Huffman coding: Greedy tree building
- Dijkstra: Greedy shortest path
- Kruskal: Greedy MST

**Backtracking:**
- Stack to track state
- Prune when impossible

**Randomized:**
- Quicksort with random pivot
- Hash tables with random hash
- Skip lists with random levels
