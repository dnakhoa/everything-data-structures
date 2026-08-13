# Chapter 21: Algorithm Design Using Data Structures

Algorithm design is usually taught as a catalog of paradigms and data structures as a separate catalog of containers. They are not separate. **Each paradigm is defined by a specific bookkeeping problem, and the paradigm becomes practical exactly when a structure solves that bookkeeping in the right complexity.**

Dijkstra's algorithm is the cleanest demonstration. The algorithm — repeatedly settle the nearest unsettled vertex — is unchanged since 1956. Its complexity is entirely a property of the structure answering "which is nearest?":

| Priority queue | Complexity | Best for |
|----------------|-----------|----------|
| Unsorted array | O(V²) | Dense graphs (E ≈ V²) |
| Binary heap | O((V + E) log V) | Sparse graphs — the usual choice |
| Fibonacci heap | O(E + V log V) | Theoretically optimal, rarely faster in practice |

Same algorithm, three complexities. This chapter reads each paradigm that way: what does it need to remember, and which structure remembers it best?

## 21.1 Divide and Conquer

Use data structures to divide problems:
- Quicksort: Partition around pivot
- Merge sort: Divide at midpoint, merge sorted halves
- Binary search: Divide search space in half

Divide and conquer splits a problem into independent subproblems, solves them recursively, and combines the results. Its bookkeeping need is **the recursion itself** — which is why the stack from [Chapter 5](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md) is the paradigm's implicit data structure. Every recursive call is a stack frame, and converting a recursive algorithm to an iterative one always means making that stack explicit.

Cost follows the Master Theorem: for T(n) = a·T(n/b) + f(n), compare f(n) against n^(log_b a). The three sorts above are the three cases in miniature — merge sort is T(n) = 2T(n/2) + O(n) = O(n log n), binary search is T(n) = T(n/2) + O(1) = O(log n).

The structural insight worth carrying: **the split and the combine trade off against each other.** Merge sort splits trivially at the midpoint and pays in the merge. Quicksort pays in the partition and combines for free. Same total, different placement — and it is why quicksort sorts in place while merge sort needs O(n) scratch space.

Where a structure changes the answer outright:

- **Segment trees** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) are divide-and-conquer made persistent. Rather than re-splitting per query, the split is stored once as a tree and reused, turning O(n) range queries into O(log n).
- **Karatsuba multiplication** and **Strassen's algorithm** win by reducing the number of subproblems — 3 instead of 4, 7 instead of 8 — so the branching factor `a` drops and the exponent falls with it.
- **Deep recursion** on user-controlled input is a stack-overflow bug. An explicit stack is not just a style preference.

## 21.2 Dynamic Programming

Optimal substructure + overlapping subproblems:
- Use memoization (hash table)
- Tabulation (array)

Dynamic programming applies when subproblems **overlap** — the case where plain divide and conquer recomputes the same work exponentially many times. Its bookkeeping need is a **map from subproblem to answer**, and the choice of map is the whole implementation decision.

**Memoization** (top-down) uses a hash table, recursion, and computes only reachable subproblems. **Tabulation** (bottom-up) uses an array, iteration, and computes all of them. The tradeoff is concrete: memoization skips unreachable states, which matters when the state space is sparse; tabulation has no recursion overhead and far better cache locality, which usually makes it faster when the state space is dense.

```python
# Memoized: sparse state space, natural recursion, hash table lookup per call
@lru_cache(maxsize=None)
def lcs(i, j):
    if i == 0 or j == 0:
        return 0
    if a[i-1] == b[j-1]:
        return 1 + lcs(i-1, j-1)
    return max(lcs(i-1, j), lcs(i, j-1))

# Tabulated with rolling rows: O(min(m, n)) space instead of O(m·n)
def lcs_table(a, b):
    if len(b) > len(a):
        a, b = b, a                       # keep the inner dimension small
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            cur[j] = 1 + prev[j-1] if a[i-1] == b[j-1] else max(prev[j], cur[j-1])
        prev = cur
    return prev[len(b)]
```

The rolling-row trick in the second version is the most broadly useful DP optimization there is: if a row depends only on the previous row, only two rows need to exist. An O(m·n) table becomes O(min(m,n)) space. Sequence alignment on genomes is feasible because of this.

Structures that change what DP can do:

- **Monotonic deque** — sliding-window maximum in O(1) amortized, turning an O(n·k) DP into O(n). The basis of the sliding-window-maximum optimization.
- **Convex hull trick / Li Chao tree** — when transitions have the form `min(m·x + b)`, maintaining the lower envelope of lines drops an O(n²) DP to O(n log n).
- **Fenwick tree** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) — when a transition sums over a prefix of previous states, prefix sums in O(log n) beat re-scanning in O(n).
- **Bitsets** — subset-sum over n items and capacity W runs in O(nW/64) rather than O(nW), a 64× constant-factor win that regularly decides feasibility.

## 21.3 Greedy Algorithms

Make locally optimal choices:
- Huffman coding: Greedy tree building
- Dijkstra's: Greedy shortest path
- Kruskal's: Greedy MST

A greedy algorithm commits to the locally best choice and never reconsiders. Its bookkeeping need is **"what is the best remaining option?"**, asked repeatedly — which is precisely the priority queue's interface. That is not a coincidence; it is why heaps appear in nearly every greedy algorithm.

Look at the three examples through their structures:

| Algorithm | Greedy choice | Structure | Complexity |
|-----------|--------------|-----------|-----------|
| Huffman coding | Merge two least-frequent nodes | Min-heap | O(n log n) |
| Dijkstra | Settle nearest unsettled vertex | Min-heap by distance | O((V+E) log V) |
| Prim's MST | Add cheapest edge leaving the tree | Min-heap by edge weight | O(E log V) |
| Kruskal's MST | Add cheapest edge that doesn't cycle | Sort + **union-find** | O(E log E) |
| Interval scheduling | Take earliest finish time | Sort by end time | O(n log n) |

Kruskal's is the interesting row, because its bookkeeping is not "what's cheapest" — sorting answers that once — but "would this edge create a cycle?" Union-find answers it in near-constant amortized time, α(n), and without union-find the cycle check would be a graph traversal per edge and the algorithm would be O(E·V). A different question needs a different structure.

**Greedy is only correct when the problem has the right structure**, and that is a genuine mathematical condition, not a hopeful assumption. The **matroid** property guarantees it — Kruskal's is correct because forests of a graph form a matroid. Absent such a property, greedy produces plausible wrong answers: it fails on 0/1 knapsack, on set cover (though it gives a ln n approximation), and on shortest paths with negative edges, which is exactly why Dijkstra requires non-negative weights. A greedy algorithm that is *nearly* right is often worse than an obviously wrong one, because nobody notices.

## 21.4 Backtracking

Systematic search with pruning:
- Use stack to track state
- Prune when impossible

Backtracking explores a decision tree depth-first, abandoning a branch as soon as it cannot lead to a solution. Its bookkeeping need is **the current partial state, cheaply undoable** — and the emphasis belongs on *undoable*, because the difference between a fast solver and a hopeless one is usually the cost of undoing a move.

The naive approach copies the state at each node, costing O(state) per branch. The right approach mutates and reverses:

```python
def solve(board, row, cols, diag1, diag2):
    """N-Queens. Sets give O(1) conflict checks; undo is symmetric with do."""
    if row == len(board):
        return True
    for col in range(len(board)):
        if col in cols or (row - col) in diag1 or (row + col) in diag2:
            continue                                    # prune
        cols.add(col); diag1.add(row - col); diag2.add(row + col)   # do
        board[row] = col
        if solve(board, row + 1, cols, diag1, diag2):
            return True
        cols.remove(col); diag1.remove(row - col); diag2.remove(row + col)  # undo
    return False
```

The three sets are the data-structure decision. Checking conflicts by scanning previously placed queens is O(n) per candidate; the sets make it O(1). Same search tree, different constant — and the constant is what makes n = 20 tractable.

Structures that make backtracking practical:

- **Bitmasks** replace those sets entirely for small n. `cols | diag1 | diag2` in three integers, with conflict-checking and undo as single instructions. This is the standard fast N-Queens.
- **Dancing Links (DLX)** — Knuth's doubly-linked-list technique for exact cover, where removing and *restoring* a row or column are both O(1) pointer updates. It is the fastest known general Sudoku and pentomino solver, and it exists entirely because of how cheap its undo is.
- **Union-find with rollback** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) provides undoable connectivity for search over graph states.
- **Trie** — in word search and Boggle solvers, a trie prunes the moment a prefix cannot extend to any word, which collapses the search space dramatically.

Constraint propagation deserves mention as the general principle: the more work you do to detect a dead end early, the smaller the tree. This is why SAT solvers spend most of their time in propagation rather than search.

## 21.5 Randomized Algorithms

Probabilistic techniques:
- Quicksort (random pivot)
- Hash tables (random hash functions)
- Skip lists (random levels)

Randomization buys two distinct things, and conflating them is a common confusion:

**Las Vegas** algorithms are always correct, with running time that varies — randomized quicksort always sorts, and is O(n log n) *expected*. **Monte Carlo** algorithms have fixed running time and may be wrong — a Bloom filter always answers in O(k), and sometimes answers wrongly.

The unifying purpose across all three examples is **defeating adversarial input**. Deterministic quicksort with a fixed pivot has an O(n²) input, and it is easy to construct — this was a real denial-of-service vector. Deterministic hashing has a collision-flooding input, which was a widely exploited DoS against web frameworks in 2011. Randomization means the adversary cannot construct a bad input in advance, because the bad input depends on choices not yet made.

| Structure | Randomization | Buys |
|-----------|--------------|------|
| Randomized quicksort | Random pivot | O(n log n) expected regardless of input |
| Skip list | Random level per node | Balance without rotations — and easy concurrency |
| Treap | Random priority | A BST balanced in expectation, trivial to implement |
| Universal hashing | Random hash from a family | Collision bounds that hold against an adversary |
| Bloom filter | k independent hashes | Membership in ~10 bits/element |
| HyperLogLog | Hash bit-pattern statistics | Cardinality of billions in 12KB |
| Reservoir sampling | Random replacement | Uniform sample of a stream of unknown length |

**Skip lists** deserve a closer look because they show randomization buying something beyond speed. A skip list and a red-black tree are both O(log n), but the skip list gets there with coin flips instead of rotations — and since insertion touches only a few forward pointers rather than rebalancing a region, skip lists are far easier to make concurrent, as [Chapter 18](ch18-concurrent-data-structures.md) discusses. Randomness bought *simplicity and locality*, and concurrency came along with them.

Two practical cautions. First, "random" must mean unpredictable to an adversary: seeding a hash function with a fixed constant, or with the process start time, reintroduces exactly the attack you were defending against. Second, expected-case bounds say nothing about any individual run — a randomized quicksort *can* be quadratic, just not reliably, and a system with hard latency requirements may need a guaranteed bound instead.

## 21.6 Choosing a Paradigm

The diagnostic question for each:

| Signal | Paradigm | Structure that makes it work |
|--------|----------|------------------------------|
| Independent subproblems | Divide and conquer | Stack (explicit if deep) |
| Overlapping subproblems, optimal substructure | Dynamic programming | Array (dense) or hash map (sparse) |
| Locally optimal choice is provably safe | Greedy | Priority queue; union-find for connectivity |
| Search a space, most branches invalid | Backtracking | Cheaply-undoable state: bitmask, DLX |
| Adversarial input, or determinism too slow | Randomized | Depends — the randomness is the technique |

And the thread running through all of them: **identify the question the algorithm asks over and over, then pick the structure that answers that question fastest.** Dijkstra asks "which is nearest." Kruskal asks "would this cycle." DP asks "have I computed this." Backtracking asks "can this branch still work." Get the question right and the structure is usually obvious; get it wrong and no amount of optimization will help.

---

## Where this connects

- [Chapter 9: Heaps and Priority Queues](../volume-1/ch09-heaps-and-priority-queues.md) — the priority queue behind every greedy algorithm
- [Chapter 11: Graphs—Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md) — the graph algorithms these paradigms produce
