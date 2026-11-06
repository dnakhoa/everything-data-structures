# Chapter 21: Algorithm Design Using Data Structures

Algorithm design is usually taught as a catalog of paradigms and data structures as a separate catalog of containers. They are not separate. **Each paradigm is defined by a specific bookkeeping problem, and the paradigm becomes practical exactly when a structure solves that bookkeeping in the right complexity.**

Dijkstra's algorithm is the cleanest demonstration. The algorithm (repeatedly settle the nearest unsettled vertex) is unchanged since 1956. Its complexity is entirely a property of the structure answering "which is nearest?":

| Priority queue | Complexity | Best for |
|----------------|-----------|----------|
| Unsorted array | O(V²) | Dense graphs (E ≈ V²) |
| Binary heap | O((V + E) log V) | Sparse graphs, the usual choice |
| Fibonacci heap | O(E + V log V) | Theoretically optimal, rarely faster in practice |

Same algorithm, three complexities. This chapter reads each paradigm that way: what does it need to remember, and which structure remembers it best?

## 21.1 Divide and Conquer

Use data structures to divide problems:
- Quicksort: Partition around pivot
- Merge sort: Divide at midpoint, merge sorted halves
- Binary search: Divide search space in half

Divide and conquer splits a problem into independent subproblems, solves them recursively, and combines the results. Its bookkeeping need is **the recursion itself**, which is why the stack from [Chapter 5](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md) is the paradigm's implicit data structure. Every recursive call is a stack frame, and converting a recursive algorithm to an iterative one always means making that stack explicit.

Cost follows the Master Theorem: for T(n) = a·T(n/b) + f(n), compare f(n) against n^(log_b a). Merge sort is T(n) = 2T(n/2) + O(n) = O(n log n), binary search is T(n) = T(n/2) + O(1) = O(log n). Both land in the middle case, where f(n) matches n^(log_b a) and the cost picks up a log factor.

The structural insight worth carrying: **the split and the combine trade off against each other.** Merge sort splits trivially at the midpoint and pays in the merge. Quicksort pays in the partition and combines for free. Same total, different placement, and it is why quicksort sorts in place while merge sort needs O(n) scratch space.

Where a structure changes the answer outright:

- **Segment trees** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) are divide-and-conquer made persistent. Rather than re-splitting per query, the split is stored once as a tree and reused, turning O(n) range queries into O(log n).
- **Karatsuba multiplication** and **Strassen's algorithm** win by reducing the number of subproblems (3 instead of 4, 7 instead of 8) so the branching factor `a` drops and the exponent falls with it.
- **Deep recursion** on user-controlled input is a stack-overflow bug. An explicit stack is not just a style preference.

## 21.2 Dynamic Programming

Optimal substructure + overlapping subproblems:
- Use memoization (hash table)
- Tabulation (array)

Dynamic programming applies when subproblems **overlap**: the case where plain divide and conquer recomputes the same work exponentially many times. Its bookkeeping need is a **map from subproblem to answer**, and the choice of map is the whole implementation decision.

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

- **Monotonic deque**: sliding-window maximum in O(1) amortized, turning an O(n·k) DP into O(n). The basis of the sliding-window-maximum optimization.
- **Convex hull trick / Li Chao tree**, when transitions have the form `min(m·x + b)`, maintaining the lower envelope of lines drops an O(n²) DP to O(n log n).
- **Fenwick tree** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)), when a transition sums over a prefix of previous states, prefix sums in O(log n) beat re-scanning in O(n).
- **Bitsets**. Subset-sum over n items and capacity W runs in O(nW/64) rather than O(nW), a 64× constant-factor win that regularly decides feasibility.

## 21.3 Greedy Algorithms

Make locally optimal choices:
- Huffman coding: Greedy tree building
- Dijkstra's: Greedy shortest path
- Kruskal's: Greedy MST

A greedy algorithm commits to the locally best choice and never reconsiders. Its bookkeeping need is **"what is the best remaining option?"**, asked repeatedly, which is precisely the priority queue's interface. That is not a coincidence; it is why heaps appear in nearly every greedy algorithm.

Look at the three examples through their structures:

| Algorithm | Greedy choice | Structure | Complexity |
|-----------|--------------|-----------|-----------|
| Huffman coding | Merge two least-frequent nodes | Min-heap | O(n log n) |
| Dijkstra | Settle nearest unsettled vertex | Min-heap by distance | O((V+E) log V) |
| Prim's MST | Add cheapest edge leaving the tree | Min-heap by edge weight | O(E log V) |
| Kruskal's MST | Add cheapest edge that doesn't cycle | Sort + **union-find** | O(E log E) |
| Interval scheduling | Take earliest finish time | Sort by end time | O(n log n) |

Kruskal's is the interesting row, because its bookkeeping is not "what's cheapest" (sorting answers that once) but "would this edge create a cycle?" Union-find answers it in near-constant amortized time, α(n), and without union-find the cycle check would be a graph traversal per edge and the algorithm would be O(E·V). A different question needs a different structure.

**Greedy is only correct when the problem has the right structure**, and that is a genuine mathematical condition, not a hopeful assumption. The **matroid** property guarantees it. Kruskal's is correct because forests of a graph form a matroid. Absent such a property, greedy produces plausible wrong answers: it fails on 0/1 knapsack, on set cover (though it gives a ln n approximation), and on shortest paths with negative edges, which is exactly why Dijkstra requires non-negative weights. A greedy algorithm that is *nearly* right is often worse than an obviously wrong one, because nobody notices.

## 21.4 Backtracking

Systematic search with pruning:
- Use stack to track state
- Prune when impossible

Backtracking explores a decision tree depth-first, abandoning a branch as soon as it cannot lead to a solution. Its bookkeeping need is **the current partial state, cheaply undoable**, and the emphasis belongs on *undoable*, because the difference between a fast solver and a hopeless one is usually the cost of undoing a move.

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

The three sets are the data-structure decision. Checking conflicts by scanning previously placed queens is O(n) per candidate; the sets make it O(1). Same search tree, different constant, and the constant is what makes n = 20 tractable.

Structures that make backtracking practical:

- **Bitmasks** replace those sets entirely for small n. `cols | diag1 | diag2` in three integers, with conflict-checking and undo as single instructions. This is the standard fast N-Queens.
- **Dancing Links (DLX)**: Knuth's doubly-linked-list technique for exact cover, where removing and *restoring* a row or column are both O(1) pointer updates. It is the fastest known general Sudoku and pentomino solver, and it exists entirely because of how cheap its undo is.
- **Union-find with rollback** ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) provides undoable connectivity for search over graph states.
- **Trie**: in word search and Boggle solvers, a trie prunes the moment a prefix cannot extend to any word, which collapses the search space dramatically.

Constraint propagation deserves mention as the general principle: the more work you do to detect a dead end early, the smaller the tree. This is why SAT solvers spend most of their time in propagation rather than search.

## 21.5 Randomized Algorithms

Probabilistic techniques:
- Quicksort (random pivot)
- Hash tables (random hash functions)
- Skip lists (random levels)

Randomization buys two distinct things, and conflating them is a common confusion:

**Las Vegas** algorithms are always correct, with running time that varies. Randomized quicksort always sorts, and is O(n log n) *expected*. **Monte Carlo** algorithms have fixed running time and may be wrong: a Bloom filter always answers in O(k), and sometimes answers wrongly.

The unifying purpose across all three examples is **defeating adversarial input**. Deterministic quicksort with a fixed pivot has an O(n²) input, and it is easy to construct, this was a real denial-of-service vector. Deterministic hashing has a collision-flooding input, which was a widely exploited DoS against web frameworks in 2011. Randomization means the adversary cannot construct a bad input in advance, because the bad input depends on choices not yet made.

| Structure | Randomization | Buys |
|-----------|--------------|------|
| Randomized quicksort | Random pivot | O(n log n) expected regardless of input |
| Skip list | Random level per node | Balance without rotations, and easy concurrency |
| Treap | Random priority | A BST balanced in expectation, trivial to implement |
| Universal hashing | Random hash from a family | Collision bounds that hold against an adversary |
| Bloom filter | k independent hashes | Membership in ~10 bits/element |
| HyperLogLog | Hash bit-pattern statistics | Cardinality of billions in 12KB |
| Reservoir sampling | Random replacement | Uniform sample of a stream of unknown length |

**Skip lists** deserve a closer look because they show randomization buying something beyond speed. A skip list and a red-black tree are both O(log n), but the skip list gets there with coin flips instead of rotations, and since insertion touches only a few forward pointers rather than rebalancing a region, skip lists are far easier to make concurrent, as [Chapter 18](ch18-concurrent-data-structures.md) discusses. Randomness bought *simplicity and locality*, and concurrency came along with them.

Two practical cautions. First, "random" must mean unpredictable to an adversary: seeding a hash function with a fixed constant, or with the process start time, reintroduces exactly the attack you were defending against. Second, expected-case bounds say nothing about any individual run. A randomized quicksort *can* be quadratic, just not reliably, and a system with hard latency requirements may need a guaranteed bound instead.

## 21.6 Choosing a Paradigm

The diagnostic question for each:

| Signal | Paradigm | Structure that makes it work |
|--------|----------|------------------------------|
| Independent subproblems | Divide and conquer | Stack (explicit if deep) |
| Overlapping subproblems, optimal substructure | Dynamic programming | Array (dense) or hash map (sparse) |
| Locally optimal choice is provably safe | Greedy | Priority queue; union-find for connectivity |
| Search a space, most branches invalid | Backtracking | Cheaply-undoable state: bitmask, DLX |
| Adversarial input, or determinism too slow | Randomized | Depends, the randomness is the technique |

And the thread running through all of them: **identify the question the algorithm asks over and over, then pick the structure that answers that question fastest.** Dijkstra asks "which is nearest." Kruskal asks "would this cycle." DP asks "have I computed this." Backtracking asks "can this branch still work." Get the question right and the structure is usually obvious; get it wrong and no amount of optimization will help.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**21.1 ★ Master Theorem cases.** For T(n) = a·T(n/b) + f(n), compare f(n) with n^(log_b a) and solve each recurrence. Say which of the three cases applies.

1. Karatsuba: T(n) = 3T(n/2) + O(n)
2. Strassen: T(n) = 7T(n/2) + O(n²)
3. Naive divide-and-conquer matrix multiplication: T(n) = 8T(n/2) + O(n²)
4. T(n) = 2T(n/2) + O(n²)

<details>
<summary>Solution</summary>

The three cases: if n^(log_b a) grows polynomially faster than f(n), the leaves dominate (case 1, T = Θ(n^(log_b a))). If they match, every level costs the same (case 2, an extra log factor). If f(n) grows polynomially faster and satisfies the regularity condition a·f(n/b) ≤ c·f(n) for some c < 1, the root dominates (case 3, T = Θ(f(n))).

| Recurrence | n^(log_b a) | f(n) | Case | T(n) |
|------------|-------------|------|------|------|
| 3T(n/2) + n | n^(log₂ 3) ≈ n^1.585 | n | 1 | Θ(n^1.585) |
| 7T(n/2) + n² | n^(log₂ 7) ≈ n^2.807 | n² | 1 | Θ(n^2.807) |
| 8T(n/2) + n² | n^(log₂ 8) = n³ | n² | 1 | Θ(n³) |
| 2T(n/2) + n² | n | n² | 3 | Θ(n²) |

For the last row, regularity holds: 2·(n/2)² = n²/2, so c = 1/2 works.

Rows 2 and 3 show the 21.1 point about Karatsuba and Strassen exactly: same f(n), but cutting a from 8 to 7 lowers the exponent from 3 to 2.807. Merge sort and binary search, from 21.1, are both case 2.

</details>

**21.2 ★ Pick Dijkstra's priority queue.** A graph has V = 10,000 vertices. Using the costs in the table at the start of this chapter (with log₂ V ≈ 13.3), estimate the work for an unsorted array and a binary heap when (a) the graph is nearly complete, E ≈ V² = 10⁸, and (b) the graph is sparse, E = 40,000. Which wins each time, and by roughly how much?

<details>
<summary>Solution</summary>

| | Unsorted array, V² | Binary heap, (V + E) log V |
|---|---|---|
| (a) E = 10⁸ | 10⁸ | ≈ 10⁸ × 13.3 ≈ 1.3 × 10⁹ |
| (b) E = 4 × 10⁴ | 10⁸ | 5 × 10⁴ × 13.3 ≈ 6.6 × 10⁵ |

(a) The **array wins by about 13×**. With E ≈ V², every edge has to be examined anyway, and the heap adds a log V factor to each one. The array's V scans of V entries cost the same order as reading the edges.

(b) The **heap wins by about 150×**. The array still pays V² regardless of how few edges exist.

The crossover is around E ≈ V² / log V. Same algorithm, and the right structure depends on a property of the input (density) rather than of the algorithm.

</details>

**21.3 ★★ Rolling-row LCS by hand.** Run `lcs_table("AGGTAB", "GXTXAYB")` from 21.2. Note the swap at the top of the function. Write out `prev` after each iteration of the outer loop. What is the result? Then explain why this version cannot tell you *which* subsequence is common, and what it would take to recover it.

<details>
<summary>Hint</summary>

After the swap, `a` is the longer string. Each row has `len(b) + 1` entries, and `cur[j]` depends only on `prev[j-1]`, `prev[j]`, and `cur[j-1]`.

</details>

<details>
<summary>Solution</summary>

`len(b) > len(a)` (7 > 6), so the strings swap: `a = "GXTXAYB"` drives the outer loop and `b = "AGGTAB"` indexes the columns.

| i | a[i−1] | prev after the iteration (columns: ∅ A G G T A B) |
|---|--------|---------------------------------------------------|
| 0 | | 0 0 0 0 0 0 0 |
| 1 | G | 0 0 1 1 1 1 1 |
| 2 | X | 0 0 1 1 1 1 1 |
| 3 | T | 0 0 1 1 2 2 2 |
| 4 | X | 0 0 1 1 2 2 2 |
| 5 | A | 0 1 1 1 2 3 3 |
| 6 | Y | 0 1 1 1 2 3 3 |
| 7 | B | 0 1 1 1 2 3 4 |

The result is `prev[6]` = **4**, for the subsequence GTAB.

The function keeps only lengths, and only two rows of them. Recovering the subsequence means walking backwards from the bottom-right cell, at each step checking whether the characters matched (move diagonally) or which neighbor the max came from (move up or left). That walk needs every row, so the simple approach keeps the full O(m·n) table. Hirschberg's algorithm gets the subsequence in O(min(m, n)) space anyway: it runs the rolling-row computation forwards on the first half of one string and backwards on the second half to find where an optimal path crosses the middle row, then recurses on the two halves. That is divide and conquer (21.1) layered on top of DP (21.2), at roughly twice the time.

</details>

**21.4 ★★ Watch greedy fail.** 21.3 says greedy fails on 0/1 knapsack. (a) With capacity 10 and items (weight, value) = (6, 30), (5, 20), (5, 20), what does "take the best value-per-weight item that still fits" choose, and what is optimal? (b) Making change with coins {1, 3, 4}, what does "take the largest coin that fits" produce for 6, and what is optimal? (c) Write the DP that always gets (b) right, and state its complexity.

<details>
<summary>Solution</summary>

(a) Ratios are 5, 4, 4. Greedy takes (6, 30), leaving capacity 4, so neither 5-weight item fits: **value 30**. The optimum skips the best-ratio item and takes both (5, 20) items: **value 40**. The first choice looked best locally and blocked a better combination.

(b) Greedy: 4, then 1, then 1, which is **3 coins**. Optimal: 3 + 3, **2 coins**.

(c) The subproblem is "fewest coins for amount x", and it overlaps heavily, so tabulate it in an array (21.2's dense case):

```python
def min_coins(coins, amount):
    INF = float('inf')
    best = [0] + [INF] * amount          # best[x] = fewest coins summing to x
    for x in range(1, amount + 1):
        for c in coins:
            if c <= x and best[x - c] + 1 < best[x]:
                best[x] = best[x - c] + 1
    return best[amount]

assert min_coins([1, 3, 4], 6) == 2
assert min_coins([1, 5, 10, 25], 63) == 6      # 25 + 25 + 10 + 1 + 1 + 1
```

It runs in O(amount × number of coins) time and O(amount) space. For the US coin set the greedy answer happens to be optimal (such coin systems are called canonical), which is exactly why the greedy habit survives: it works on the examples people try first.

</details>

**21.5 ★★ Kruskal with union-find.** Run Kruskal's algorithm on this graph, processing edges in increasing weight. For each edge, say whether `find` puts its endpoints in the same set, and whether the edge is accepted or rejected.

```
Edges (weight: endpoints)
1: A-B   2: B-C   3: A-C   4: C-D   5: B-D   6: D-E   7: C-E
```

What is the MST's total weight? How much work would the cycle check cost per edge without union-find?

<details>
<summary>Solution</summary>

| Edge | Sets before | Same set? | Decision | Sets after |
|------|-------------|-----------|----------|------------|
| 1: A-B | {A} {B} {C} {D} {E} | no | accept | {A,B} {C} {D} {E} |
| 2: B-C | {A,B} {C} {D} {E} | no | accept | {A,B,C} {D} {E} |
| 3: A-C | {A,B,C} {D} {E} | yes | reject (cycle A-B-C) | unchanged |
| 4: C-D | {A,B,C} {D} {E} | no | accept | {A,B,C,D} {E} |
| 5: B-D | {A,B,C,D} {E} | yes | reject | unchanged |
| 6: D-E | {A,B,C,D} {E} | no | accept | {A,B,C,D,E} |
| 7: C-E | one set | yes | reject | unchanged |

MST edges: A-B, B-C, C-D, D-E, total weight **1 + 2 + 4 + 6 = 13**. After the fourth acceptance (V − 1 = 4 edges) the algorithm could stop.

Without union-find, each "would this create a cycle?" check is a traversal of the forest built so far, which has up to V − 1 edges: O(V) per edge, O(E·V) overall. With union-find (union by rank and path compression), each check is O(α(V)) amortized, so the sort, O(E log E), dominates.

</details>

**21.6 ★★ Sliding-window maximum.** 21.2 cites the monotonic deque. Implement `window_max(xs, k)`, which returns the maximum of every window of k consecutive elements in O(n) total. Trace it on `[1, 3, -1, -3, 5, 3, 6, 7]` with k = 3, showing the deque's values after each element. Then justify the O(n) bound.

<details>
<summary>Hint</summary>

Store indices, not values, and keep their values decreasing from front to back. A new element makes every smaller element behind it useless forever.

</details>

<details>
<summary>Solution</summary>

```python
from collections import deque

def window_max(xs, k):
    dq = deque()                     # indices; their values decrease front to back
    out = []
    for i, x in enumerate(xs):
        while dq and xs[dq[-1]] <= x:
            dq.pop()                 # dominated: older and no larger than x
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()             # front has left the window
        if i >= k - 1:
            out.append(xs[dq[0]])
    return out

assert window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
```

| i | x | Deque values after | Output |
|---|---|--------------------|--------|
| 0 | 1 | [1] | |
| 1 | 3 | [3] (1 popped) | |
| 2 | −1 | [3, −1] | 3 |
| 3 | −3 | [3, −1, −3] | 3 |
| 4 | 5 | [5] (−3, −1, 3 popped) | 5 |
| 5 | 3 | [5, 3] | 5 |
| 6 | 6 | [6] (3, 5 popped) | 6 |
| 7 | 7 | [7] (6 popped) | 7 |

**Why O(n):** each index is appended exactly once and removed at most once (from the back by a larger element, or from the front by leaving the window). So across the whole run there are at most n appends and n removals, even though a single step can pop many elements, as at i = 4. That is O(1) amortized per element. A popped element is safe to discard because the newer, larger x will be in every future window that the popped one would have been in.

</details>

**21.7 ★★★ Bitmask N-Queens.** 21.4 says bitmasks replace the three sets in `solve` for small n. Write `count_queens(n)` that counts *all* solutions using three integers: occupied columns, and the two diagonal directions shifted so that bit positions line up with the current row. Verify n = 8 gives 92. Explain why the diagonal masks shift by one bit per row.

<details>
<summary>Hint</summary>

`free & -free` isolates the lowest set bit of `free`.

</details>

<details>
<summary>Solution</summary>

```python
def count_queens(n):
    full = (1 << n) - 1                        # n ones: every column

    def place(cols, d1, d2):
        if cols == full:                       # one queen in every column: solved
            return 1
        total = 0
        free = full & ~(cols | d1 | d2)        # columns not attacked in this row
        while free:
            bit = free & -free                 # lowest free column
            free ^= bit                        # remove it from the candidates
            total += place(cols | bit,
                           ((d1 | bit) << 1) & full,
                           (d2 | bit) >> 1)
        return total

    return place(0, 0, 0)

assert [count_queens(n) for n in range(1, 11)] == [1, 0, 0, 2, 10, 4, 40, 92, 352, 724]
```

**Why the shifts.** A queen at column c attacks column c + 1 in the next row along one diagonal and column c − 1 along the other, then c + 2 and c − 2 a row later, and so on. Rather than store diagonal ids (`row − col`, `row + col` in the set version), the masks store *which columns in the current row* each diagonal family attacks. Moving down one row moves every attack one column over, which is a shift left by one for one family and right by one for the other. `& full` drops attacks that slide off the board; the right shift drops them automatically.

**Why it is faster.** The conflict check that took three hash lookups per candidate column is one `~(cols | d1 | d2)` for the whole row, and the loop visits only the free columns instead of testing all n. Undo is free: each recursive call receives new integers, so there is nothing to remove afterwards. This is the 21.4 principle taken to its limit, where state is cheap enough to pass by value, so undo disappears.

</details>

---

## Where this connects

- [Chapter 9: Heaps and Priority Queues](../volume-1/ch09-heaps-and-priority-queues.md). The priority queue behind every greedy algorithm
- [Chapter 11: Graphs—Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md). The graph algorithms these paradigms produce
