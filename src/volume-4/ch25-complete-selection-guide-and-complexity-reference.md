# Chapter 25: Complete Selection Guide and Complexity Reference

This chapter is for the moment you have a problem and need a structure. Section 25.1 maps common needs to choices, split by whether the data is static or changing. Sections 25.2 and 25.3 are the reference tables. Section 25.4 gives a short decision procedure for when no row of the matrix fits exactly, Section 25.5 works through six realistic selection problems end to end, and Section 25.6 lists the mistakes that come up again and again in code review.

## 25.1 Data Structure Selection Matrix

Most selection questions turn on one distinction first: is the data **static** (built once, queried many times) or does it **change** between queries? Static data admits simpler, faster, smaller structures, and that column is often the right answer even when it looks too simple.

| Need | Static data | With updates | Notes |
|------|-------------|--------------|-------|
| Lookup by exact key | Sorted array + binary search; perfect hashing for a fixed key set | Hash table (Robin Hood or Swiss table, [Chapter 12](../volume-2/ch12-hash-tables.md)) | A hash table gives up ordering; if you will ever need "next key" or a range, see the next row |
| Ordered map: successor, range scans | Sorted array | Red-black tree or skip list in memory; B+ tree on disk | Sorted arrays win for read-heavy data even with occasional bulk rebuilds |
| Integer keys below u: predecessor | Sorted array | B-tree or radix tree in practice; vEB or y-fast trie in theory ([Chapter 24](ch24-research-grade-data-structures.md)) | The O(log log u) structures rarely beat a cache-friendly B-tree below about 10⁷ keys |
| Repeated minimum or maximum | Sorted array | Binary heap (4-ary is often faster); indexed heap if you need decrease-key; radix heap for monotone integer keys | A balanced BST also works and supports deletion of arbitrary keys |
| Range sum | Prefix sums, O(1) query | Fenwick tree (point updates); segment tree with lazy propagation (range updates) | |
| Range minimum or maximum | Sparse table, O(1) query; Fischer-Heun RMQ in 2n + o(n) bits | Segment tree | Idempotence (min(x, x) = x) is what lets a sparse table use overlapping windows |
| k-th smallest overall, rank of a key | Sorted array | Order-statistic tree; Fenwick tree over compressed values | Redis sorted sets use a skip list with span counts |
| k-th smallest in a subarray a[l..r] | Wavelet tree or wavelet matrix | Offline techniques, or a Fenwick tree of order-statistic trees in O(log² n) | |
| Path or subtree queries on a tree | Heavy-light decomposition + segment tree | Link-cut tree when edges are linked and cut | Euler tour + segment tree handles subtree aggregates |
| Connectivity | Union-find, when edges are only added | Offline with deletions: rollback DSU over a segment tree of time; online: HDT (research) | |
| Find one pattern in a text | KMP, Z-algorithm, or the language's built-in search | | Rabin-Karp when many windows must be compared |
| Find many patterns in one pass | Aho-Corasick | | |
| Many queries against one fixed text | Suffix array + LCP; FM-index when it must be compressed | Suffix automaton supports appending | |
| Palindromes | Manacher's algorithm (all maximal palindromes in O(n)) | Palindromic tree (distinct palindromes, append-only) | |
| Approximate membership | Bloom filter; xor filter for a fixed set | Cuckoo filter (supports deletion); quotient filter | |
| Count of distinct items | HyperLogLog | HyperLogLog | Mergeable across machines |
| Item frequencies, heavy hitters | Count-Min sketch; Space-Saving for top-k | Same | |
| Quantiles over a stream | t-digest, KLL | Same | |
| Cache | | LRU (hash map + doubly linked list); W-TinyLFU for skewed workloads | [Chapter 29](../volume-5/ch29-system-design-as-data-structure-composition.md) |
| Text being edited | | Piece table or rope; gap buffer for a single cursor | [Chapter 13](../volume-2/ch13-string-data-structures.md) |

## 25.2 Complete Complexity Reference

### Competitive Programming Structures

| Structure | Build | Query | Update | Space |
|-----------|-------|-------|--------|-------|
| Segment Tree | O(n) | O(log n) | O(log n) | O(n) |
| Fenwick Tree | O(n) | O(log n) | O(log n) | O(n) |
| Heavy-Light Decomp | O(n) | O(log² n) | O(log² n) | O(n) |
| Link-Cut Tree | O(n) | O(log n) amortized | O(log n) amortized | O(n) |
| DSU with rollback | O(n) | O(log n) | O(log n) | O(n) |
| Mo's Algorithm | n/a | O(√n) amortized per query | n/a | O(n) |
| Sparse Table | O(n log n) | O(1) | Not supported | O(n log n) |
| Wavelet Tree | O(n log σ) | O(log σ) | Static | O(n log σ) |
| Suffix Automaton | O(n) | O(m) | Incremental | O(n), ≤ 2n−1 states |
| Palindromic Tree | O(n) | O(1) amortized | Incremental | O(n) |
| Li Chao Tree | O(n log C) | O(log C) | O(log C) | O(n) |

Two rows are easy to get wrong. **DSU with rollback is O(log n), not O(α(n))**. Undoing a union requires knowing exactly which parent pointers changed, and path compression rewrites pointers all along the path, so rollback DSU must use union by rank alone. You trade the inverse-Ackermann bound for the ability to undo. And **Mo's algorithm is offline**: it answers q queries in O((n + q)√n) *total*, so the O(√n) is an amortized per-query share, not a bound on any individual query.

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

★ = amortized. **H_k(T)** is the k-th order empirical entropy of the text. The FM-index is compressed to the text's own entropy, which is what "self-indexing" means: you can discard the original text and still reconstruct any substring.

## 25.3 Algorithm Design Patterns

Each paradigm is defined by a bookkeeping question it must answer repeatedly, and becomes practical when a structure answers that question fast enough. [Chapter 21](../volume-3/ch21-algorithm-design-using-data-structures.md) develops this in full; the summary:

| Paradigm | Question asked repeatedly | Structure that answers it | Examples |
|----------|--------------------------|---------------------------|----------|
| Divide and conquer | Where do I resume? | Stack (implicit or explicit) | Quicksort, merge sort, binary search |
| Dynamic programming | Have I computed this state? | Array (dense) or hash map (sparse) | LCS, knapsack, edit distance |
| Greedy | What is the best remaining option? | Priority queue; union-find for connectivity | Huffman, Dijkstra, Prim, Kruskal |
| Backtracking | Can this branch still succeed, and how cheaply do I undo? | Bitmask, DLX, rollback DSU | N-Queens, Sudoku, exact cover |
| Randomized | (Defeat the adversary) | Depends, randomness *is* the technique | Quicksort, skip lists, treaps, Bloom filters |

The recurring trap: greedy is only correct when the problem has the matroid property or an equivalent exchange argument. Without it, greedy produces plausible wrong answers, which is worse than obviously wrong ones, because they pass casual testing.

## 25.4 A Decision Procedure

When no row of the matrix fits exactly, five questions, asked in order, usually narrow the choice to one or two candidates.

1. **What are the operations, and in what proportion?** Write them down with rough frequencies: "10⁶ lookups per second, 10³ inserts per second, a range scan per minute". Most bad choices come from optimising an operation that is rare. A structure that makes the common operation O(1) and the rare one O(n) is often right.
2. **Is the data static, append-only, or fully dynamic?** Static data allows sorted arrays, sparse tables, perfect hashing and succinct structures, all of which are smaller and faster than their dynamic counterparts. Append-only data allows logs, LSM trees and suffix automata.
3. **Does order matter?** If any query mentions "next", "range", "smallest", "top" or "before", you need an ordered structure (sorted array, balanced tree, B-tree, skip list, heap). If every query is "is this key present, and what is its value", a hash table is almost always the answer.
4. **Does it fit in memory, and on one machine?** If not, the cost model changes from operations to block transfers ([Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md)): B+ trees and LSM trees on one machine, partitioned structures across several ([Chapter 27](../volume-5/ch27-distributed-data-structures.md)).
5. **Can the answer be approximate?** If a small, bounded error is acceptable, a probabilistic structure ([Chapter 14](../volume-3/ch14-probabilistic-data-structures.md)) can be thousands of times smaller. If it must be exact and the exact structure fits in memory, use the exact one.

<figure>
{{#include ../images/selection-flowchart.svg}}
<figcaption>Questions 2 to 5 as a flowchart, for the common case of storing keys and looking them up. It is a starting point, not a verdict; Section 25.5 shows how workload details change the answer.</figcaption>
</figure>

After choosing, check the answer against three practical constraints the asymptotics ignore: memory per element (a Python dict entry costs around 100 bytes once you include the key and value objects, so 50 million entries need about 5 GB), worst-case latency (amortized and expected bounds allow occasional slow operations), and whether a well-tested library already provides it ([Chapter 22](../volume-3/ch22-practical-considerations.md)).

## 25.5 Worked Selection Problems

Each problem states the workload, the choice, the cost, and why the obvious alternatives lose.

### Autocomplete over a fixed vocabulary

**Workload.** Ten million product names, each with a popularity score, rebuilt nightly. Each keystroke asks for the 10 most popular names starting with the typed prefix, at thousands of queries per second.

**Choice.** The data is static, so sort the names. All names with a given prefix form one contiguous block of the sorted array, found with two binary searches. Inside the block, the top 10 by popularity come from a sparse table of "index of the maximum score" (Section 23.11) and a heap: take the maximum of the block, split the block around it, push the maximum of each half, and repeat 10 times.

```python
import heapq
from bisect import bisect_left


class Autocomplete:
    """Top-k most popular completions of a prefix, over a fixed vocabulary."""

    def __init__(self, words_with_scores):
        pairs = sorted(words_with_scores)               # sort by word
        self.words = [w for w, _ in pairs]
        self.score = [s for _, s in pairs]
        n = len(pairs)
        # Sparse table of argmax over the scores (Chapter 23.11).
        self.table = [list(range(n))]
        j = 1
        while (1 << j) <= n:
            prev, half = self.table[-1], 1 << (j - 1)
            row = []
            for i in range(n - (1 << j) + 1):
                a, b = prev[i], prev[i + half]
                row.append(a if self.score[a] >= self.score[b] else b)
            self.table.append(row)
            j += 1

    def _argmax(self, lo, hi):                          # best index in [lo, hi)
        j = (hi - lo).bit_length() - 1
        a, b = self.table[j][lo], self.table[j][hi - (1 << j)]
        return a if self.score[a] >= self.score[b] else b

    def complete(self, prefix, k):
        lo = bisect_left(self.words, prefix)
        hi = bisect_left(self.words, prefix + '￿')  # end of the prefix block
        heap, out = [], []
        if lo < hi:
            i = self._argmax(lo, hi)
            heap.append((-self.score[i], i, lo, hi))
        while heap and len(out) < k:
            _, i, a, b = heapq.heappop(heap)
            out.append(self.words[i])
            for x, y in ((a, i), (i + 1, b)):           # split around the winner
                if x < y:
                    m = self._argmax(x, y)
                    heapq.heappush(heap, (-self.score[m], m, x, y))
        return out
```

**Cost.** O(n log n) to build, once a night. Each query is O(log n) for the binary searches plus O(k log k) for the heap, independent of how many names match the prefix. With "car" typed, the block might hold 50,000 names; the query still touches only about 2k of them.

**Why not the alternatives?** A trie answers the prefix part in O(prefix length) but then must explore every completion to find the most popular, unless each trie node stores its own top 10, which multiplies memory by the average depth. Scanning the block and sorting by popularity costs O(block size) per keystroke, which is fine for long prefixes and fatal for "a".

### A live leaderboard

**Workload.** 50 million players, each with an integer score between 0 and 10⁶. Scores change constantly. Queries: a player's rank, and the top 100.

**Choice.** Two options are both good, and the score range decides. A general **order-statistic structure** (a skip list with span counts, as in Redis sorted sets, or a size-augmented balanced tree, [Chapter 7](../volume-1/ch07-binary-search-trees.md)) gives O(log n) update and rank for any score type. Because scores here are bounded integers, a **Fenwick tree indexed by score** that counts players per score value is smaller and faster: an update is two point updates (remove the old score, add the new one), and a rank is one prefix sum, each O(log 10⁶), about 20 steps, in a 4 MB array. Ties are broken separately (for example by time reached).

**Why not the alternatives?** Sorting on every query is O(n log n), seconds per query at 50 million. A hash map from player to score answers "what is my score" but not "what is my rank".

### Has the crawler seen this URL?

**Workload.** A web crawler has seen 5 billion URLs and checks each newly discovered link before fetching it. The full URL set lives in an on-disk key-value store.

**Choice.** A **Bloom filter** in memory in front of the on-disk store. At a 1% false-positive rate it needs about 9.6 bits per URL, which is about 6 GB for 5 billion URLs, with 7 hash functions. A "not present" answer is always correct, so new URLs (the common case for a crawler at the frontier) never touch the disk. A "present" answer is checked against the store, which catches the 1% of false positives.

**Why not the alternatives?** An exact in-memory hash set of 5 billion URLs at an average of 70 bytes each needs well over 350 GB. Checking the disk store for every link costs a random read per link. The Bloom filter is the classic case of question 5 in Section 25.4: approximate is acceptable because an exact check backs it up.

### A rate limiter for an API

**Workload.** A million API keys, each allowed 100 requests per minute, checked on every request.

**Choice.** A **hash map from API key to a token bucket** (two numbers: tokens remaining and last refill time, [Chapter 29](../volume-5/ch29-system-design-as-data-structure-composition.md)). Each check is O(1) expected and the whole table is tens of megabytes.

**When it changes.** If the keys are unbounded (rate limiting by client IP during an attack, say), the map can be made to grow without limit. Then a **Count-Min sketch** per time window bounds memory regardless of the number of distinct clients. It never undercounts, so it never lets an abuser through; at worst it rate-limits a few legitimate clients early.

### Meeting rooms and overlapping intervals

**Workload.** A calendar service stores bookings as [start, end) intervals per room and must reject any new booking that overlaps an existing one.

**Choice.** Bookings in one room never overlap one another, so a **balanced ordered map keyed by start time** is enough: a new interval [s, e) conflicts only with the booking whose start is the floor of s (does it end after s?) or the ceiling of s (does it start before e?). Two O(log n) lookups ([Chapter 7](../volume-1/ch07-binary-search-trees.md), floor and ceiling). An **interval tree** is needed only when stored intervals may overlap one another, for example when the query is "which of all these events are happening at 3 pm?"

### Latency percentiles across a fleet

**Workload.** A thousand servers each record request latencies; a dashboard shows the fleet-wide p50, p99 and p99.9 every minute.

**Choice.** A **t-digest** (or a KLL sketch) per server per minute, a few kilobytes each, merged centrally ([Chapter 14](../volume-3/ch14-probabilistic-data-structures.md)). Mergeability is the deciding property: you cannot average per-server p99s to get the fleet p99, but you can merge the sketches and query the merged one.

**Why not the alternatives?** Shipping every raw latency costs gigabytes per minute. Fixed histogram buckets work if you know the range in advance, and HdrHistogram is a good choice when you do; t-digest needs no such tuning and is most accurate at the extreme percentiles you care about.

## 25.6 Common Selection Mistakes

- **A hash map when the queries need order.** The code then sorts the keys on every request. If any query mentions a range or "the next one", choose an ordered structure up front.
- **A linked list for "fast insertion".** Insertion is O(1) only once you hold the node, and finding it is O(n) with a cache miss per step. A dynamic array usually wins even for insertions in the middle ([Chapter 22](../volume-3/ch22-practical-considerations.md) has the measurements).
- **Linear operations hidden in a library call.** `x in some_list`, `list.pop(0)` and `list.insert(0, x)` in Python are all O(n). Inside a loop they quietly make an algorithm quadratic.
- **Choosing by asymptotic bounds alone.** Fibonacci heaps, van Emde Boas trees and many other theoretical winners lose to simpler structures at realistic sizes because of constant factors and cache behaviour.
- **Approximate structures where exact ones fit.** A Bloom filter for 10,000 keys saves a few hundred kilobytes and adds false positives to debug. Use probabilistic structures when the exact one does not fit, or when mergeability or a fixed memory budget matters.
- **Ignoring worst-case latency.** Amortized O(1) includes the occasional O(n) resize, and expected O(1) includes the occasional long probe sequence. For a latency-sensitive path, preallocate, or choose structures with worst-case bounds.
- **Distributing too early.** A structure that fits on one machine is far simpler and faster than any distributed one. Check the memory arithmetic before reaching for a cluster.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**25.1 ★ Pick from the matrix.** For each workload, name the structure you would use from Sections 25.1 and 25.2 and the per-operation cost you get. (a) A static array of 10^6 integers and 10^6 range-minimum queries. (b) An array with interleaved point updates and range-sum queries. (c) An array with interleaved "add v to every element in [l, r]" and "sum of [l, r]". (d) A static array and queries "the k-th smallest value in a[l..r]".

<details>
<summary>Solution</summary>

| Workload | Choice | Cost |
|----------|--------|------|
| (a) static range min | Sparse table | O(n log n) build, O(1) query |
| (b) point update, range sum | Fenwick tree | O(log n) each |
| (c) range add, range sum | Segment tree with lazy propagation | O(log n) each |
| (d) static range k-th smallest | Wavelet tree | O(log σ) query after O(n log σ) build |

(a) has no updates and min is idempotent, so the overlapping-window trick applies and nothing beats O(1). (b) is exactly what a Fenwick tree does, with the smallest code and memory. (c) needs range updates: a plain Fenwick tree only supports point updates, so use the lazy segment tree of Chapter 23 (or the two-Fenwick-tree trick, which is less general). (d) is the wavelet tree's defining query; a merge sort tree also works but costs O(log² n) or worse per query.

</details>

**25.2 ★ The greedy trap.** Section 25.3 says greedy is only correct with a matroid property or an exchange argument. (a) Disprove: "To make change with the fewest coins, repeatedly take the largest coin that fits." Use coins {1, 3, 4} and amount 6. (b) Name the structure that the table pairs with greedy, and explain why using it does not rescue (a).

<details>
<summary>Solution</summary>

(a) Greedy takes 4, then 1, then 1: **3 coins**. The optimum is 3 + 3: **2 coins**. The claim is false. (It happens to hold for coin systems like {1, 5, 10, 25}, which is why it passes casual testing, the exact failure mode the section warns about.)

(b) The table pairs greedy with a priority queue ("what is the best remaining option?"). A priority queue makes each greedy choice fast; it says nothing about whether the choice is correct. Here the "best remaining option" is answered in O(log n) and is still the wrong option. The correct method for arbitrary coin systems is dynamic programming over amounts, which the same table pairs with an array: `best[x] = 1 + min(best[x − c])` over coins c, O(amount × coins).

</details>

**25.3 ★★ Amortized, offline, or worst case?** A trading system must answer every request within a fixed latency budget, and requests arrive one at a time. For each of the following rows from Section 25.2, say whether the stated bound protects a single request, and give a concrete situation in which a single operation is much slower than the table entry suggests: (a) Fibonacci heap delete-min, (b) link-cut tree path query, (c) Mo's algorithm, (d) DSU with rollback.

<details>
<summary>Hint</summary>

The ★ in the table marks amortized bounds. One row is not amortized at all, it is offline.

</details>

<details>
<summary>Solution</summary>

(a) **Amortized only.** After n inserts (each O(1), just a new root in the root list), the first delete-min must consolidate all n roots: Θ(n) for that single call. The amortized O(log n) is paid for by the cheap inserts before it.

(b) **Amortized only.** Link-cut trees rest on splay trees. A single `access` can splay through a splay tree of depth Θ(n) (for example after a run of operations that left a path-shaped splay tree), costing Θ(n) once, with the cost recovered over later operations.

(c) **Not applicable at all.** Mo's algorithm is offline: it sorts all queries before answering any. With requests arriving one at a time it cannot run. The O(√n) "per query" is a share of an O((n + q)√n) total.

(d) **Worst case per operation.** With union by size and no path compression, every tree has depth at most log₂ n, so every `find` and `union` is O(log n) with no amortization. This is the one structure of the four whose bound you can quote for a single request.

For the latency budget, prefer worst-case structures (binary heap over Fibonacci heap, a red-black or AVL tree over a splay tree) and accept slightly worse averages.

</details>

**25.4 ★★ Prove the rollback DSU bound.** Section 25.2 says rollback DSU uses union by rank (or size) alone and costs O(log n). Using the `DSU` class of Section 23.14, which links the smaller-size root under the larger, prove that every node has depth at most ⌊log₂ n⌋. Then explain why `rollback` cannot break the bound.

<details>
<summary>Hint</summary>

Ask what has to happen to the size of a node's set each time that node's depth increases by one.

</details>

<details>
<summary>Solution</summary>

Pick any node x. Its depth only changes when its root `r` is linked under another root `r'` in `union`, and that increases the depth of every node in `r`'s tree, including x, by exactly 1. The code links `y` under `x` only after swapping so that `size[x] ≥ size[y]`, so `size[r'] ≥ size[r]`. After the link, x's set has size `size[r] + size[r'] ≥ 2 · size[r]`: it at least doubled.

x starts in a set of size 1, and no set exceeds n, so x's set can double at most ⌊log₂ n⌋ times. Hence depth(x) ≤ ⌊log₂ n⌋, and `find`, which walks from x to its root, costs O(log n). `union` is two finds plus O(1).

`rollback` pops logged changes in reverse order, restoring `parent[y]` and `size[x]` exactly. Each state it restores is a state the structure was in earlier, which satisfied the bound when it was built. Path compression is what would break rollback: it rewrites pointers that are never logged (Exercise 23.5), so "restoring" would produce a state that never existed.

</details>

**25.5 ★★ Sparse table or segment tree at n = 10^6?** You have a static array of n = 10^6 integers, q range-minimum queries, and a 64 MB memory limit, with 4-byte integers. (a) How many rows does the `SparseTable` of Section 23.11 build, and how much memory does it use? (b) How much does an array-based segment tree with `4n` slots use? (c) Which do you choose, and how would your answer change if the limit were 256 MB and q = 10^7?

<details>
<summary>Solution</summary>

(a) `self.k = log[n] + 1`. Since 2^19 = 524,288 ≤ 10^6 < 2^20, `log[10^6] = 19` and there are **20 rows**. The chapter's code allocates n slots per row: `20 × 10^6 = 2 × 10^7` integers, **80 MB**. (Trimming row k to its `n − 2^k + 1` valid entries saves only about 5%: the top rows are shorter, but most rows are nearly full length.)

(b) `4 × 10^6` integers, **16 MB**. An iterative bottom-up segment tree needs only `2n`, 8 MB.

(c) At 64 MB the sparse table does not fit, so use the segment tree: O(n) build, O(log n) query, about 2 · 20 node visits per query plus pushes. At 256 MB with q = 10^7, the sparse table fits and wins clearly: its build is about 2 × 10^7 `op` calls, and each query is two lookups, about 2 × 10^7 lookups total, versus several hundred million node visits for the segment tree. The row in Section 25.2 (O(n log n) space, O(1) query) is the whole tradeoff: memory for query time, and only for static data with an idempotent operation.

</details>

**25.6 ★★★ Offline dynamic connectivity.** Section 25.1 lists an offline approach for connectivity when edges can also be removed. You are given the whole sequence of operations in advance: `('add', u, v)`, `('remove', u, v)` and `('query', u, v)` ("are u and v connected right now?"). A plain DSU cannot delete edges. Using the rollback `DSU` of Section 23.14 and a segment tree over time, write `offline_connectivity(n, ops)` that returns the query answers in order, and state its running time.

<details>
<summary>Hint</summary>

Each edge is alive during one contiguous interval of operation indices. Insert it into the O(log T) segment tree nodes that cover that interval, then walk the tree depth-first: union a node's edges on entry, answer queries at leaves, and roll back on exit.

</details>

<details>
<summary>Solution</summary>

```python
def offline_connectivity(n, ops):
    """ops: list of ('add', u, v), ('remove', u, v) or ('query', u, v).
    Returns the answers to the queries, in order."""
    T = len(ops)
    if T == 0:
        return []
    seg = [[] for _ in range(4 * T)]

    def insert(node, l, r, ql, qr, edge):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            seg[node].append(edge)
            return
        mid = (l + r) // 2
        insert(2 * node, l, mid, ql, qr, edge)
        insert(2 * node + 1, mid + 1, r, ql, qr, edge)

    start = {}                      # edge -> time it was added
    for t, (kind, u, v) in enumerate(ops):
        e = (min(u, v), max(u, v))
        if kind == 'add':
            start[e] = t
        elif kind == 'remove':
            insert(1, 0, T - 1, start.pop(e), t - 1, e)
    for e, s in start.items():      # never removed: alive to the end
        insert(1, 0, T - 1, s, T - 1, e)

    dsu = DSU(n)
    answers = [None] * T

    def solve(node, l, r):
        snap = dsu.snapshot()
        for u, v in seg[node]:
            dsu.union(u, v)
        if l == r:
            kind, u, v = ops[l]
            if kind == 'query':
                answers[l] = dsu.find(u) == dsu.find(v)
        else:
            mid = (l + r) // 2
            solve(2 * node, l, mid)
            solve(2 * node + 1, mid + 1, r)
        dsu.rollback(snap)

    solve(1, 0, T - 1)
    return [a for a, op in zip(answers, ops) if op[0] == 'query']

ops = [('add', 0, 1), ('add', 1, 2), ('query', 0, 2),
       ('remove', 0, 1), ('query', 0, 2), ('add', 0, 2), ('query', 0, 1)]
assert offline_connectivity(3, ops) == [True, False, True]
```

Why it is correct: when the DFS reaches leaf t, the DSU contains exactly the edges stored on the root-to-leaf path, and an edge is stored on that path iff its alive interval contains t. So the DSU is the graph at time t. Rollback on exit restores the state of the parent, which is why path compression is not allowed here (Exercise 25.4).

Cost: each edge lands in O(log T) segment tree nodes, and each of those causes one `union` and one undo at O(log n). Total **O(T log T log n)**, plus O(T) for the tree. This is the offline alternative to Holm–de Lichtenberg–Thorup: much simpler, no amortization, but it needs every operation up front. If queries must be answered as they arrive, you are back to HDT's O(log² n) amortized updates.

</details>

**25.7 ★★ The leaderboard, by hand and in code.** Section 25.5 suggests a Fenwick tree indexed by score for a leaderboard with bounded integer scores. (a) Five players have scores 3, 5, 5, 1 and 7, with scores between 0 and 7. A player's rank is 1 plus the number of players with a strictly higher score. Give the rank of a player with each score 7, 5, 3 and 1, and say which prefix sum computes each. (b) The player with score 1 improves to 6. What changes in the tree, and what are the new ranks? (c) Implement it.

<details>
<summary>Hint</summary>

The number of players with a strictly higher score than s is the total minus the number with score at most s, and "at most s" is a prefix sum over the count array.

</details>

<details>
<summary>Solution</summary>

(a) Counts per score: 1 player at 1, 1 at 3, 2 at 5, 1 at 7, total 5. Rank(s) = 1 + 5 − (players with score ≤ s):

| Score | Players ≤ score (prefix sum) | Rank |
|-------|------------------------------|------|
| 7 | 5 | 1 |
| 5 | 4 | 2 |
| 3 | 2 | 4 |
| 1 | 1 | 5 |

Both players with score 5 share rank 2, and the next rank is 4: standard competition ranking.

(b) Two point updates: subtract 1 at score 1, add 1 at score 6, each O(log 8). Scores are now 3, 5, 5, 6, 7, and the ranks of 7, 6, 5, 3 are 1, 2, 3, 5.

(c)

```python
class ScoreLeaderboard:
    """Rank queries for integer scores in [0, max_score], via a Fenwick tree."""

    def __init__(self, max_score):
        self.n = max_score + 1
        self.tree = [0] * (self.n + 1)            # 1-indexed Fenwick tree
        self.total = 0

    def _add(self, score, delta):
        i = score + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def _count_at_most(self, score):              # players with score <= s
        i, s = score + 1, 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def add_player(self, score):
        self._add(score, 1)
        self.total += 1

    def change(self, old, new):
        self._add(old, -1)
        self._add(new, 1)

    def rank(self, score):
        """1 + number of players with a strictly higher score."""
        return 1 + self.total - self._count_at_most(score)
```

Every operation is O(log S) for S possible scores, regardless of the number of players, and the memory is S + 1 integers. For scores up to 10⁶ that is about 20 steps per operation in a 4 MB array.

</details>

**25.8 ★★ Room bookings without an interval tree.** Section 25.5 claims that for one room, where stored bookings never overlap, an ordered map keyed by start time is enough to reject overlapping bookings. (a) Explain why a new booking [s, e) can only conflict with the stored booking that starts at or just after s, or the one just before it. (b) Implement `can_book` with two sorted lists and `bisect`, and trace the bookings [9, 10), [13, 15), [10, 13), [9, 11), [14, 16), [8, 9) in that order. (c) When does this stop being enough?

<details>
<summary>Solution</summary>

(a) Stored bookings are disjoint, so sorted by start they are also sorted by end. Every booking after the first one starting at or after s starts even later, so if that first one starts at or after e, all later ones do too. Every booking before the one just before s ends no later than that one does, so if it ends at or before s, all earlier ones do too. Checking those two neighbours is enough.

(b)

```python
from bisect import bisect_left


def can_book(starts, ends, s, e):
    """starts is sorted; bookings [starts[i], ends[i]) never overlap."""
    i = bisect_left(starts, s)                    # first booking starting at or after s
    if i < len(starts) and starts[i] < e:         # it starts before we end
        return False
    if i > 0 and ends[i - 1] > s:                 # the one before ends after we start
        return False
    return True


def book(starts, ends, s, e):
    if not can_book(starts, ends, s, e):
        return False
    i = bisect_left(starts, s)
    starts.insert(i, s)
    ends.insert(i, e)
    return True
```

Trace, with half-open intervals so that touching is allowed:

| Request | Result | Why |
|---------|--------|-----|
| [9, 10) | booked | empty |
| [13, 15) | booked | no neighbour overlaps |
| [10, 13) | booked | touches [9, 10) and [13, 15) but overlaps neither |
| [9, 11) | rejected | the booking starting at 9 starts before 11 |
| [14, 16) | rejected | [13, 15) ends after 14 |
| [8, 9) | booked | touches [9, 10) |

`can_book` is O(log n). With Python lists, `book` is O(n) because of `insert`; a balanced tree or `sortedcontainers.SortedList` makes it O(log n).

(c) It relies on stored intervals never overlapping. If they can overlap (several rooms in one structure, or "show every event at 3 pm" over arbitrary events), sorting by start no longer sorts by end, and an interval tree or a segment tree over time is needed.

</details>

---

## Where this connects

- [Chapter 22: Practical Considerations](../volume-3/ch22-practical-considerations.md). The practical version of this decision process
