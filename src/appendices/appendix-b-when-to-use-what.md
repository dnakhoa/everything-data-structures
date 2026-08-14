# Appendix B: When to Use What

## B.1 The Short Answer

| Need | Structure |
|------|----------|
| Fast lookup by key | Hash table |
| Ordered data | Balanced BST, B+ tree |
| Range queries | B+ tree, segment tree |
| Priority access | Heap |
| LIFO | Stack |
| FIFO | Queue |
| Graph traversal | Adjacency list |
| String prefix | Trie |
| Approximate membership | Bloom filter |
| Approximate counting | HyperLogLog |
| 2D spatial | R-tree, KD-tree |
| 3D spatial | Octree |

## B.2 The Decision, in Four Questions

Most structure choices resolve with these, asked in order.

**1. Do I ever need the elements in order?**

This is the single most consequential question, and the one most often skipped. Ordered iteration, range queries, "the next key after X", and "the smallest key" all require a tree or a sorted structure. A hash table can do none of them at any price.

The failure mode is not discovering this on day one — it is discovering it six months in, when someone asks for "all records between these two dates" and the answer requires replacing the container.

| Order needed? | Go to |
|---------------|-------|
| No — point lookups only | Hash table |
| Yes | Balanced BST (in memory), B+ tree (on disk) |
| Only by priority, one at a time | Heap |
| Only by prefix | Trie or radix tree |

**2. What is the read/write mix?**

| Pattern | Favors |
|---------|--------|
| Read-heavy, rarely changes | Sorted array, perfect hash, immutable structure |
| Balanced | Hash table, balanced BST |
| Write-heavy | LSM tree, append-only log |
| Append-only | Dynamic array, log |

**3. Where does it live?**

| Location | Constraint | Choose |
|----------|-----------|--------|
| CPU cache / small | Constant factors dominate | Array, linear scan |
| RAM | Pointer chasing costs | Hash table, B-tree (not BST) |
| Disk / SSD | Block transfers dominate | B+ tree, LSM tree |
| Across machines | Round trips dominate | Consistent hashing, CRDT, DHT |

**4. How exact must it be?**

If an approximate answer is acceptable, the space savings are usually one to five orders of magnitude — but check which way the errors go first ([Chapter 14](../volume-3/ch14-probabilistic-data-structures.md)).

## B.3 By Operation

The structure that makes each operation cheapest, with the cost of choosing it.

| Operation | Best choice | Cost of that choice |
|-----------|------------|---------------------|
| Lookup by key | Hash table, O(1) | No ordering at all |
| Lookup by index | Array, O(1) | Insertion in the middle is O(n) |
| Min or max | Heap, O(1) | Arbitrary search is O(n) |
| k-th smallest | Order-statistic tree, O(log n) | Extra size field per node |
| Predecessor / successor | Balanced BST, O(log n) | Slower than a hash table for point lookups |
| Range query | B+ tree or segment tree, O(log n + k) | Higher write cost |
| Prefix match | Trie, O(P) | Memory per node |
| Insert at both ends | Deque, O(1) | No O(1) middle insertion |
| Insert in the middle given a position | Linked list, O(1) | Finding the position is O(n) |
| Merge two collections | Leftist / pairing heap, O(log n) | Slower than a binary heap otherwise |
| Membership, huge set | Bloom filter, O(k) | False positives; no enumeration |
| Count distinct | HyperLogLog, O(1) | ~2% error |
| Connectivity under merging | Union-find, O(α(n)) | Cannot split |

## B.4 By Scale

The right answer changes with n, and the changes are larger than intuition suggests.

| n | What actually wins |
|---|-------------------|
| < 100 | A flat array and a linear scan. One cache line at a time, perfect prefetching, no hashing. Clever structures usually lose here. |
| 10³–10⁶ | Hash tables, balanced trees. Classic complexity analysis applies cleanly. |
| 10⁶–10⁹ | Cache and memory layout dominate. Prefer B-trees over BSTs, arrays over pointer chains. |
| > RAM | External memory model. B+ trees, LSM trees, memory-mapped files. |
| > one machine | Sharding, consistent hashing, replication. Coordination becomes the cost. |

## B.5 Common Mistakes

**Using a linked list because insertion is O(1).** It is O(1) only once you already hold the node. Finding it is O(n), and the traversal is cache-hostile. `std::vector` beats `std::list` for middle insertion at surprisingly large sizes — measure before believing otherwise.

**Using a hash map when you needed order.** See B.2, question 1. This is the most expensive mistake on this page because it surfaces late.

**Reaching for a fancy structure at small n.** A segment tree over 50 elements is slower than a loop, and considerably more code to get wrong.

**Ignoring the worst case on untrusted input.** A hash table is O(1) average and O(n) adversarial. If users can choose the keys, you need a keyed hash or a treeifying table ([Chapter 12](../volume-2/ch12-hash-tables.md)).

**Optimizing before profiling — and profiling the wrong thing.** If a function is slow and the arithmetic is trivial, the problem is memory, and only hardware counters will show it ([Chapter 22](../volume-3/ch22-practical-considerations.md)).

**Testing with random data.** Real data arrives sorted far more often than random data does — by timestamp, by ID, by insertion order. Sorted input is the worst case for a naive BST and for quicksort with a fixed pivot. Test sorted, reverse-sorted, and all-identical deliberately.

## B.6 Language Defaults

What to reach for first, per language, before writing anything custom.

| Need | Python | Java | C++ | Go | Rust |
|------|--------|------|-----|-----|------|
| Hash map | `dict` | `HashMap` | `unordered_map` | `map` | `HashMap` |
| Ordered map | — (use `sortedcontainers`) | `TreeMap` | `map` | — | `BTreeMap` |
| Dynamic array | `list` | `ArrayList` | `vector` | slice | `Vec` |
| Deque | `collections.deque` | `ArrayDeque` | `deque` | — | `VecDeque` |
| Heap | `heapq` (min only) | `PriorityQueue` | `priority_queue` (max) | `container/heap` | `BinaryHeap` (max) |
| Set | `set` | `HashSet` | `unordered_set` | `map[T]struct{}` | `HashSet` |
| Ordered set | — | `TreeSet` | `set` | — | `BTreeSet` |

Two traps worth remembering: Python has **no ordered map or tree in the standard library** — `dict` preserves insertion order, which is not the same as sorted order. And `heapq` is min-only while C++ and Rust default to max-heaps, which is a reliable source of inverted-comparator bugs when porting.

For fuller detail on what these are actually implemented as, see [Chapter 22](../volume-3/ch22-practical-considerations.md); for exact complexities, [Appendix A](appendix-a-complexity-cheat-sheet.md).
