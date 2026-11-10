# Appendix A: Complexity Cheat Sheet

Two conventions for reading these tables:

- **Average** assumes random or well-distributed data. **Worst** is the adversarial case. Where they differ, the gap is usually the whole story. A hash table is O(1) average and O(n) worst, and which one you get depends on your hash function and your adversary.
- ★ marks **amortized** bounds: cheap on average across a sequence of operations, with occasional expensive ones. A dynamic array append is O(1)★ because the resize that costs O(n) happens rarely enough to average out.

## A.1 Linear Structures

| Structure | Access by index | Search by value | Insert | Delete | Space |
|-----------|----------------|-----------------|--------|--------|-------|
| Static array | O(1) | O(n) | n/a | n/a | O(n) |
| Sorted array | O(1) | O(log n) | O(n) | O(n) | O(n) |
| Dynamic array | O(1) | O(n) | O(1)★ at end, O(n) elsewhere | O(n) | O(n) |
| Singly linked list | O(n) | O(n) | O(1) given the node | O(1) given the previous node | O(n) |
| Doubly linked list | O(n) | O(n) | O(1) given the node | O(1) given the node | O(n) |
| Stack | n/a | O(n) | O(1)★ | O(1)★ | O(n) |
| Queue | n/a | O(n) | O(1)★ | O(1)★ | O(n) |
| Deque | O(1) | O(n) | O(1)★ at either end | O(1)★ at either end | O(n) |
| Circular buffer (fixed capacity) | O(1) | O(n) | O(1) at the rear | O(1) at the front | O(capacity) |
| Bit array | O(1) | O(n/w) | O(1) set a bit | O(1) clear a bit | n bits |
| Persistent vector (32-way trie) | O(log₃₂ n) | O(n) | O(log₃₂ n) append, path copied | O(log₃₂ n) update | O(n), shared between versions |
| Finger tree | O(log n) by index; O(1)★ at the ends | O(n) | O(1)★ at either end | O(1)★ at either end | O(n) |
| Gap buffer (text) | O(1) | O(n) | O(1) at the cursor, O(distance) to move it | O(1) at the cursor | O(n) |
| Rope (text) | O(log n) | O(n) | O(log n) anywhere | O(log n) anywhere | O(n) |
| Piece table (text, list of k pieces) | O(k) | O(n) | O(k), text itself never moves | O(k) | O(n + k) |

Where **w** = machine word size in bits.

The linked-list rows come with the caveat that makes them much less useful than they look: insertion and deletion are O(1) **only once you already hold the relevant node**. Getting there is O(n), so an insert-at-position is O(n) overall.

## A.2 Trees and Ordered Maps

| Structure | Search (avg) | Search (worst) | Insert | Delete | Space |
|-----------|-------------|----------------|--------|--------|-------|
| BST (unbalanced) | O(log n) | O(n) | O(log n) / O(n) | O(log n) / O(n) | O(n) |
| AVL tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Red-black tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Splay tree | O(log n)★ | O(n) single op | O(log n)★ | O(log n)★ | O(n) |
| Left-leaning red-black tree | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| Treap | O(log n) expected | O(n) | O(log n) expected | O(log n) expected | O(n) |
| Skip list | O(log n) expected | O(n) | O(log n) expected | O(log n) expected | **O(n) expected** |
| B-tree / B+ tree | O(log_B n) I/Os | O(log_B n) I/Os | O(log_B n) | O(log_B n) | O(n) |
| Order-statistic tree (size-augmented balanced BST) | O(log n) select / rank | O(log n) | O(log n) | O(log n) | O(n) |
| van Emde Boas tree (integer keys < u) | O(log log u) | O(log log u) | O(log log u) | O(log log u) | O(u), or O(n log log u) hashed |
| y-fast trie (integer keys < u) | O(log log u) | O(log log u) | O(log log u)★ | O(log log u)★ | O(n) |
| Trie | O(L) | O(L) | O(L) | O(L) | O(N·A) |
| Radix / Patricia trie | O(L) | O(L) | O(L) | O(L) | O(N) |

Where **L** = key length, **N** = total characters stored across all keys, **A** = alphabet size.

On a BST of height h, successor, predecessor, floor and ceiling are O(h), and reporting every key in a range is O(h + k) for k results. A B-tree with minimum degree t has height at most log_t((n+1)/2); with t = 500, a billion keys fit in 4 levels. ([Chapter 7](../volume-1/ch07-binary-search-trees.md), [Chapter 10](../volume-1/ch10-multiway-search-trees-and-b-trees.md))

AVL insertion needs at most one single or double rotation, but AVL deletion may rotate at every level on the way up, O(log n) rotations. Red-black trees need at most 2 rotations per insert and 3 per delete, plus O(log n) recolourings ([Chapter 8](../volume-1/ch08-self-balancing-trees.md)).

Two rows worth reading carefully. **Skip list space is O(n) expected**, not O(n log n): with promotion probability p = ½, the expected total number of nodes across all levels is 2n. The O(log n) is the expected *height*, which is a different quantity. And **splay trees** have no per-operation guarantee at all: a single access can cost O(n), and only a sequence of m operations is bounded, at O(m log n). That makes them unsuitable for latency-sensitive work regardless of their excellent amortized behavior.

## A.3 Hash-Based Structures

| Structure | Search (avg) | Search (worst) | Insert | Delete | Space |
|-----------|-------------|----------------|--------|--------|-------|
| Hash table (chaining) | O(1) | O(n) | O(1)★ | O(1) | O(n + m) |
| Hash table (open addressing) | O(1) | O(n) | O(1)★ | O(1) | O(m) |
| Robin Hood hashing | O(1) | O(n) | O(1)★ | O(1), backward shift | O(m) |
| Swiss table | O(1) | O(n) | O(1)★ | O(1) | O(m) plus 1 control byte per slot |
| Cuckoo hashing | O(1) | **O(1) worst case** | O(1)★ expected | O(1) | O(n) |
| Perfect hashing (static) | O(1) | O(1) | n/a | n/a | O(n) |

Where **m** = number of buckets. Cuckoo hashing is the notable row: it is one of the few hash schemes with a genuine O(1) *worst-case* lookup, because a key can only live in one of two positions. Insertion pays for it, and can fail and require a full rehash.

Robin Hood hashing has the same *average* probe length as plain linear probing; what it improves is the variance, so the longest probe sequence and the cost of an unsuccessful lookup (which can stop early) drop sharply at high load. ([Chapter 12](../volume-2/ch12-hash-tables.md))

Java's `HashMap` converts a bucket to a red-black tree past 8 entries, giving O(log n) rather than O(n) in the worst case: a defense against deliberate collision flooding.

## A.4 Heaps and Priority Queues

| Structure | Find min | Insert | Delete min | Decrease key | Merge | Space |
|-----------|----------|--------|-----------|--------------|-------|-------|
| Binary heap | O(1) | O(log n) | O(log n) | O(log n) | O(n) | O(n) |
| Indexed binary heap (position map) | O(1) | O(log n) | O(log n) | O(log n), and O(1) to locate the item | O(n) | O(n) |
| d-ary heap | O(1) | O(log_d n) | O(d·log_d n) | O(log_d n) | O(n) | O(n) |
| Binomial heap | O(log n) | O(1)★ | O(log n) | O(log n) | O(log n) | O(n) |
| Fibonacci heap | O(1) | O(1) | O(log n)★ | O(1)★ | O(1) | O(n) |
| Pairing heap | O(1) | O(1) | O(log n)★ | o(log n)★, exact bound open | O(1) | O(n) |

Building a heap from n existing elements is **O(n)**, not O(n log n): Floyd's bottom-up heapify. This surprises people and is worth remembering.

The pairing heap's decrease-key is known to be Ω(log log n)★ (Fredman, 1999) and o(log n)★ (Pettie's 2005 bound is O(2^(2√(log log n)))★), but its exact cost is still an open problem.

Fibonacci heaps have the best bounds on this table and lose to binary heaps on most real workloads; see [Chapter 19](../volume-3/ch19-emerging-and-specialized-structures.md).

## A.5 Graphs

For a graph with V vertices and E edges:

| Operation | Adjacency list | Adjacency matrix | CSR (static) |
|-----------|---------------|------------------|--------------|
| Space | O(V + E) | O(V²) | O(V + E), no pointers |
| Add edge | O(1) | O(1) | O(V + E) rebuild |
| Check edge (u,v) | O(deg(u)) | O(1) | O(log deg(u)) if sorted |
| Iterate neighbors of u | O(deg(u)) | O(V) | O(deg(u)), sequential |
| BFS / DFS | O(V + E) | O(V²) | O(V + E) |

| Algorithm | Complexity | Requires |
|-----------|-----------|----------|
| BFS / DFS | O(V + E) | n/a |
| Cycle detection (directed, three-colour DFS) | O(V + E) | n/a |
| Bipartiteness check (BFS 2-colouring) | O(V + E) | n/a |
| Topological sort (Kahn or DFS) | O(V + E) | DAG; Kahn also detects cycles |
| Strongly connected components (Kosaraju, Tarjan) | O(V + E) | Directed graph |
| 0-1 BFS | O(V + E) | Edge weights 0 or 1 |
| DAG shortest paths | O(V + E) | DAG, any weights |
| Dijkstra (binary heap) | O((V + E) log V) | Non-negative weights |
| Dijkstra (Fibonacci heap) | O(E + V log V) | Non-negative weights |
| Bellman-Ford | O(V·E) | Detects negative cycles |
| Floyd-Warshall | O(V³) | All pairs; negative edges but no negative cycles |
| Johnson's algorithm | O(V·E log V) | All pairs, sparse graphs, negative edges |
| Kruskal MST | O(E log E) | Union-find |
| Prim MST (binary heap) | O(E log V) | n/a |
| Union-Find (path compression + union by rank) | O(α(n)) ★ | n/a |
| **Union-Find with rollback** | **O(log n)** | No path compression |

That last row is a common trap. Rollback requires undoing parent changes, which path compression makes impossible to track cheaply, so rollback DSU uses union by rank alone and costs O(log n), not O(α(n)).

α(n) is the inverse Ackermann function, below 5 for any n that fits in the observable universe.

## A.6 Probabilistic and Specialized

| Structure | Query | Insert | Space | Error |
|-----------|-------|--------|-------|-------|
| Bloom filter | O(k) | O(k) | ~1.44·log₂(1/ε)·n bits | False positives only |
| Counting Bloom filter | O(k) | O(k) | 4× a Bloom filter | False positives only |
| Cuckoo filter | O(1) | O(1)★ | ~(log₂(1/ε) + 3)·n bits | False positives; supports delete |
| HyperLogLog | O(1) | O(1) | O(log log n) bits per register; 12 KB in the standard configuration | ~0.81% standard error with 16,384 registers (1.04/√m) |
| Roaring bitmap | O(log c) to find the container, then O(1) or O(log 4096) | O(log c), plus up to 4,096 shifted values in an array container | ≤ 16 bits per value within a container | None, exact |
| Count-Min Sketch | O(k) | O(k) | O((1/ε)·log(1/δ)) | Overestimates only |
| Skip list | O(log n) expected | O(log n) expected | O(n) expected | None, exact |

Where **c** = number of non-empty Roaring containers (at most 65,536 for 32-bit values).

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
| Mo's algorithm | n/a | O(√n) ★ per query | n/a | O(n) |
| Heavy-light decomposition | O(n) | O(log² n) | O(log² n) | O(n) |
| Link-cut tree | O(n) | O(log n)★ | O(log n)★ | O(n) |
| Wavelet tree | O(n log σ) | O(log σ) | Static | O(n log σ) |
| Suffix array (SA-IS) | O(n) | O(m log n) | Static | O(n) |
| Suffix automaton | O(n) | O(m) | Incremental | O(n), ≤ 2n−1 states |
| Suffix tree | O(n) | O(m) | Static | O(n) |
| Palindromic tree (eertree) | O(n) | O(1)★ | Incremental | O(n) |
| Li Chao tree | O(n log C) by n inserts | O(log C) | O(log C) | O(n) |

Where **σ** = alphabet size, **m** = pattern length, **C** = coordinate range.

Mo's algorithm is offline and processes q queries in O((n + q)√n) *total*; the O(√n) figure is the amortized per-query share, not a bound on any single query.

## A.8 Array and Sequence Techniques

| Technique | Time | Extra space | Requires |
|-----------|------|-------------|----------|
| Binary search (lower / upper bound) | O(log n) | O(1) | Sorted array |
| Binary search on the answer | O(log R) predicate calls | O(1) | Monotone predicate over a range of size R |
| Two pointers | O(n) | O(1) | Sorted array (for pair-sum style problems) |
| Sliding window (fixed or variable) | O(n) | O(1) | Non-negative values for the variable "sum ≥ target" form |
| Prefix sums (1-D) | O(n) build, O(1) range sum | O(n) | Static array |
| Prefix sums (2-D) | O(rc) build, O(1) rectangle sum | O(rc) | Static r × c matrix |
| Difference array | O(1) per range add, O(n) to rebuild | O(n) | All updates before reads |
| Monotonic stack (next greater element) | O(n) total, amortized | O(n) | n/a |
| Monotonic deque (sliding-window maximum) | O(n) total, amortized | O(k) | n/a |
| In-place linked-list reversal | O(n) | O(1) | n/a |
| Floyd's cycle detection | O(μ + λ) | O(1) | n/a |
| Merge sort on a linked list | O(n log n) | O(log n) stack, O(1) bottom-up | n/a |

Where **μ** = distance to the cycle and **λ** = cycle length.

| String matching | Preprocess | Search a text of length n | Notes |
|-----------------|-----------|---------------------------|-------|
| KMP (prefix function) | O(m) | O(n) worst case | Never backs up in the text |
| Z-algorithm | O(n + m) total | O(n + m) worst case | Search P + separator + T |
| Rabin-Karp (rolling hash) | O(m) | O(n + m) expected | Random base and a large prime; verify matches to make it exact |
| Aho-Corasick (many patterns) | O(total pattern length) | O(n + number of matches) | One pass for every pattern |
| Suffix array (search) | O(n) to O(n log n) build | O(m log n) per query | Index the text once, query many patterns |

| Posting-list intersection (lists of length m ≤ n) | Time |
|---------------------------------------------------|------|
| Linear merge | O(m + n) |
| Galloping (exponential) search | O(m log(n/m)) |
| Skip pointers | Between the two, depending on skip spacing |

## A.9 Caches and Load Balancing

| Structure | Per access | Metadata per entry | Scan-resistant |
|-----------|-----------|--------------------|----------------|
| LRU (hash map + doubly linked list) | O(1) | Two pointers | No |
| LFU (frequency buckets) | O(1) | Pointers plus a count | Yes, but slow to forget |
| CLOCK (second chance) | O(1) amortized | One reference bit | No |
| ARC | O(1) | Pointers, plus ghost lists | Yes |
| W-TinyLFU | O(1) | Pointers, plus a shared Count-Min sketch | Yes |

| Load balancing rule | Maximum load, n requests into n servers |
|---------------------|-----------------------------------------|
| Uniformly random | Θ(log n / log log n) with high probability |
| Power of d choices (d ≥ 2) | ln ln n / ln d + Θ(1) with high probability |

See [Chapter 29](../volume-5/ch29-system-design-as-data-structure-composition.md) for the simulations behind both tables.

## A.10 Allocators, Clocks and Routing

| Memory allocator | malloc | free | Fragmentation |
|------------------|--------|------|---------------|
| Implicit free list, first fit | O(blocks) | O(1) with boundary tags | External; depends on placement policy |
| Segregated free lists (size classes) | O(1) typical | O(1) | Internal, bounded by class spacing (about 20% in jemalloc) |
| Buddy system | O(log M) splits | O(log M) merges | Internal, up to about 50% from rounding to a power of two |
| Slab (fixed-size objects) | O(1) | O(1) | Little, for objects of one size |
| Arena / bump | O(1) | Only all at once | None until reset |

Where **M** = the size of the managed region in units of the smallest block ([Chapter 2](../volume-1/ch02-primitive-types-and-memory-organization.md)).

| Logical clock | Timestamp size | Detects concurrency? | Close to wall-clock time? |
|---------------|----------------|----------------------|---------------------------|
| Lamport clock | O(1) | No | No |
| Vector clock | O(n) for n processes | Yes | No |
| Hybrid logical clock | O(1) | No | Yes, within the clock skew |

| Routing lookup (W-bit addresses, N prefixes) | Memory reads per lookup | Memory |
|---------------------------------------------|------------------------|--------|
| Binary trie | Up to W | Up to 1 + N·W nodes |
| Multibit trie, stride k | ⌈W/k⌉ | Grows with 2^k per node (controlled prefix expansion) |
| DIR-24-8 (IPv4) | 1 for prefixes up to /24, else 2 | 32 MB first-level table plus second-level blocks |
| Maglev table (ECMP / load balancing) | 1 hash and 1 table read | O(M) for a prime table size M |

## A.11 Complexity Growth Reference

How the classes actually behave, for intuition about when each becomes infeasible:

| n | O(log n) | O(n) | O(n log n) | O(n²) | O(2ⁿ) |
|---|---------|------|-----------|-------|-------|
| 10 | 3 | 10 | 33 | 100 | 1,024 |
| 100 | 7 | 100 | 664 | 10,000 | 10³⁰ |
| 1,000 | 10 | 1,000 | 9,966 | 10⁶ | n/a |
| 10⁶ | 20 | 10⁶ | 2×10⁷ | 10¹² | n/a |
| 10⁹ | 30 | 10⁹ | 3×10¹⁰ | 10¹⁸ | n/a |

Rough practical ceilings at roughly 10⁸ simple operations per second: O(n²) is fine to n ≈ 10,000; O(n log n) to n ≈ 10⁷; O(n) to n ≈ 10⁸; O(2ⁿ) to n ≈ 25; O(n!) to n ≈ 11.
