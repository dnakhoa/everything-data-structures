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

**25.6 ★★★ Offline dynamic connectivity.** The matrix lists "DSU (offline)" for dynamic connectivity. You are given the whole sequence of operations in advance: `('add', u, v)`, `('remove', u, v)` and `('query', u, v)` ("are u and v connected right now?"). A plain DSU cannot delete edges. Using the rollback `DSU` of Section 23.14 and a segment tree over time, write `offline_connectivity(n, ops)` that returns the query answers in order, and state its running time.

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

---

## Where this connects

- [Chapter 22: Practical Considerations](../volume-3/ch22-practical-considerations.md). The practical version of this decision process
