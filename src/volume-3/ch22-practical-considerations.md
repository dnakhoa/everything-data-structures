# Chapter 22: Practical Considerations

Everything up to here has been about what structures *are*. This chapter is about the decisions you actually make on a Tuesday afternoon: which one to reach for, what your language already gives you, what to do when it's too slow, and how to find the bug when it's wrong.

## 22.1 Choosing the Right Structure

**Questions to ask:**
1. What operations are most frequent?
2. What is the access pattern?
3. How large is the data?
4. What are the memory constraints?
5. Is thread safety required?

Those five questions are the right ones. Here is how to actually use them.

**Start with question 1, and be specific about proportions.** "I need lookups and inserts" is not an answer; "99% lookups, 1% inserts, no iteration" is. The ratio decides everything. A sorted array beats a hash table for a read-mostly set that fits in cache, and loses catastrophically the moment writes are frequent.

**Question 2 is the one people skip and shouldn't.** Sequential access and random access are different problems, and [Chapter 16](ch16-external-memory-and-cache-oblivious-structures.md) explains why the gap is 10–100×, not 10–20%. Ask specifically: do I ever need the elements *in order*? That single question separates hash tables from trees, and it is the most common source of a wrong initial choice: people reach for a hash map, then discover six months later that they need ordered iteration.

**Question 3 changes which model applies.** Under ~1,000 elements, constant factors dominate and a linear scan of an array frequently beats every "better" structure. It is one cache line at a time with perfect prefetching, and there is no hashing or pointer-chasing. Above what fits in RAM, the external memory model applies and B-trees or LSM trees are the only serious options.

A decision table for the common cases:

| Need | Reach for | Not |
|------|-----------|-----|
| Key → value, any order | Hash table | Tree (slower, more memory) |
| Key → value, sorted iteration or range queries | Balanced BST / B-tree | Hash table (no order at all) |
| Append and index by position | Dynamic array | Linked list |
| Insert/remove at both ends | Deque | Array (O(n) at the front) |
| Repeatedly extract min or max | Binary heap | Sorted array (O(n) insert) |
| Membership only, huge set, false positives OK | Bloom filter | Hash set (10–100× the memory) |
| Prefix search, autocomplete | Trie / radix tree | Hash table (prefixes need order) |
| Connectivity under merging | Union-find | Graph traversal per query |
| Range sum / range min with updates | Fenwick or segment tree | Recomputing the range |
| Under ~100 items | Array, honestly | Anything clever |

**Question 5 deserves a warning.** "Is thread safety required?" is often answered too fast, in both directions. Wrapping every structure in a lock because the application is multithreaded is how you get a program that is slower than the single-threaded version. Conversely, a structure reachable from two threads without synchronization is broken even if it has never visibly failed. The best answer is usually to avoid sharing at all: see [Chapter 18](ch18-concurrent-data-structures.md).

## 22.2 Language-Specific Collections

| Language | Key Collections |
|----------|-----------------|
| Python | list, dict, set, tuple |
| Java | ArrayList, HashMap, TreeMap, PriorityQueue |
| C++ | vector, unordered_map, map, priority_queue |
| JavaScript | Array, Object, Map, Set |
| Go | slice, map |
| Rust | Vec, HashMap, BTreeMap, BTreeSet |

What matters is what those names are *actually implemented as*, because the names hide real differences:

| Collection | Implementation | Worth knowing |
|-----------|----------------|---------------|
| Python `dict` | Open addressing, compact + insertion-ordered since 3.7 | Ordering is a language guarantee now, not an accident |
| Python `list` | Dynamic array, ~1.125× growth | `insert(0, x)` is O(n), use `collections.deque` |
| Java `HashMap` | Chaining; buckets become red-black trees past 8 entries | The treeification defends against collision DoS |
| Java `TreeMap` | Red-black tree | Sorted iteration, `floorKey`/`ceilingKey` |
| C++ `std::map` | Red-black tree | Ordered, `unordered_map` is the hash table |
| C++ `std::vector` | Dynamic array, typically 1.5–2× growth | `reserve()` when the size is known |
| C++ `std::list` | Doubly linked | Almost always the wrong choice; `vector` wins even for middle insertion at small n |
| Go `map` | Open addressing with 8-slot buckets | Iteration order is *deliberately randomized* |
| Rust `HashMap` | SwissTable (hashbrown), SipHash by default | Swap in `FxHash` for non-adversarial internal use |
| Rust `BTreeMap` | B-tree, not a BST | Cache-friendlier than a red-black tree |
| JS `Object` vs `Map` | Hidden classes vs real hash map | `Map` for dynamic keys; `Object` keys are strings/symbols |

Three practical notes that catch people repeatedly:

- **Go randomizes map iteration order on purpose**, so that code cannot come to depend on it. If you need order, sort the keys.
- **Rust's default hasher is SipHash**, chosen to resist collision attacks, and it is measurably slower than a non-cryptographic hash. For internal maps with trusted keys, `FxHashMap` is often 2× faster.
- **C++ `std::list` is nearly always a mistake.** The textbook case for a linked list (cheap insertion in the middle) loses to `std::vector` at surprisingly large n, because finding the insertion point requires a traversal and the traversal is cache-hostile. Measure before believing otherwise.

## 22.3 Performance Optimization

- **Profiling first**: Don't optimize without measuring
- **Cache awareness**: Sequential access > random access
- **Memory pools**: Reduce allocation overhead
- **Object pooling**: Reuse frequently allocated objects

**Profile first, and profile the right thing.** A wall-clock profiler tells you where time goes; it does not tell you *why*. If a function is slow and the arithmetic is trivial, the answer is usually memory, and you need hardware counters to see it:

```bash
perf stat -e cache-misses,cache-references,instructions,cycles ./program
```

An instructions-per-cycle figure below ~1.0 with a high cache-miss rate means the CPU is waiting on memory, and no amount of algorithmic micro-tuning will help, the layout is the problem. Above ~2.0 IPC, you are compute-bound and the algorithm is the thing to change. This single distinction redirects more optimization effort than any other measurement.

**The optimization ladder**, roughly in order of payoff per unit of effort:

1. **Better algorithm or structure.** O(n²) → O(n log n) beats every constant-factor trick combined. This is where the leverage is, and the rest of this book is about it.
2. **Better memory layout.** Struct-of-arrays over array-of-structs; contiguous over pointer-chasing; shrink the hot struct so more fits per cache line. Often 2–10×.
3. **Fewer allocations.** Pre-size containers (`reserve`, `make([]T, 0, n)`). Reuse buffers. Arena-allocate objects with a shared lifetime. Allocation is rarely the headline cost, but allocation *churn* wrecks locality and GC pause times.
4. **Batching.** Amortize per-operation overhead, one bulk insert instead of n inserts, one syscall instead of n.
5. **Micro-optimization.** Branch elimination, SIMD, intrinsics. Real, but last, and easily undone by the next compiler version.

**On object pooling specifically:** it is a genuine win for expensive-to-construct objects (database connections, threads, large buffers) and frequently a net loss for cheap ones in a garbage-collected language. Modern generational GCs allocate by bumping a pointer and collect short-lived objects nearly for free; a pool converts those into long-lived objects that survive into the old generation and must be traced on every major collection. Pool connections, not integers.

**On premature pessimization**, which is the more common error than premature optimization: choosing an O(n) structure where an O(1) one was equally convenient, copying a large object where a reference would do, or building a string in a loop with `+=`. None of these are "optimizations" to skip. They are defaults to get right the first time.

## 22.4 Debugging Data Structure Bugs

- **Invariants**: Check them during development
- **Visualization**: Draw the structure
- **Testing**: Property-based testing (QuickCheck)
- **Assertions**: Validate preconditions and postconditions

Data structure bugs have a characteristic signature: the structure is *silently* wrong long before anything visibly fails. A corrupted red-black tree keeps answering queries: it just answers some of them incorrectly, and the crash comes later, somewhere else. This is why the techniques below emphasize *detection near the cause* rather than debugging at the point of failure.

**Write the invariant checker first.** For every structure, there is a predicate that must hold after every operation. Write it as code, not as a comment:

```python
def check_bst(node, lo=float('-inf'), hi=float('inf')):
    """Every BST bug this catches would otherwise surface as a wrong query."""
    if node is None:
        return True
    if not (lo < node.key < hi):
        return False
    return (check_bst(node.left, lo, node.key)
            and check_bst(node.right, node.key, hi))

def check_heap(a, i=0):
    l, r = 2*i + 1, 2*i + 2
    for c in (l, r):
        if c < len(a) and (a[i] > a[c] or not check_heap(a, c)):
            return False
    return True
```

Note that `check_bst` must thread bounds down the recursion. The version that only compares each node to its immediate children is the classic wrong answer: it accepts trees that violate the BST property across subtrees.

Then run the checker after every mutation in debug builds:

```python
def insert(self, key):
    self._insert(key)
    assert self._check_invariants(), f"invariant broken inserting {key}"
```

This turns a bug that would surface a thousand operations later into one that surfaces on the operation that caused it. For a red-black tree, check all five properties; for a B-tree, check occupancy bounds and uniform leaf depth; for union-find, check that no parent chain cycles.

**Property-based testing is the highest-value testing technique for this domain**, because data structure correctness is naturally expressible as properties, and random generation finds the edge cases you did not think of: empty, single element, duplicates, exactly-at-capacity:

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_matches_reference(items):
    """The structure must behave identically to an obviously-correct model."""
    mine, reference = MyBST(), set()
    for x in items:
        mine.insert(x); reference.add(x)
    assert sorted(mine.in_order()) == sorted(reference)

@given(st.lists(st.integers()), st.integers())
def test_search_agrees(items, probe):
    mine = MyBST()
    for x in items:
        mine.insert(x)
    assert mine.contains(probe) == (probe in items)
```

That first pattern (**model-based testing against a simple, obviously-correct reference implementation**)is the most effective single technique for validating a data structure. Your red-black tree should behave exactly like a sorted list; your LRU cache should behave exactly like an ordered dict with manual eviction. The reference can be absurdly slow; it only has to be right.

Hypothesis (Python), QuickCheck (Haskell), proptest (Rust), and jqwik (Java) all shrink failing cases automatically, so a failure on a 500-element list is reported as the 3-element list that actually breaks it.

**Visualize when the invariant checker says "broken" but not why.** Graphviz output is about ten lines of code and worth every one:

```python
def to_dot(node, out):
    if node is None:
        return
    for child, side in ((node.left, 'L'), (node.right, 'R')):
        if child:
            out.append(f'  "{node.key}" -> "{child.key}" [label="{side}"];')
            to_dot(child, out)
```

**For memory bugs** (use-after-free, double-free, buffer overruns in hand-written C structures) reach for the sanitizers rather than reasoning: `-fsanitize=address` and `-fsanitize=undefined` find in seconds what code review misses for weeks. For concurrent structures, `-fsanitize=thread`, Java's JCStress, or Rust's `loom` are effectively mandatory; a race that has not manifested in testing is not a race that does not exist.

**A checklist for the specific bug classes that recur:**

| Symptom | Usual cause |
|---------|-------------|
| Works until it doesn't, at a suspiciously round size | Resize/rehash logic |
| Wrong answer, no crash | Broken invariant, write the checker |
| Crash far from the real problem | Memory corruption, run ASan |
| Fails only under load | Race, run TSan |
| Fails only on the empty or single-element case | Missing base case; sentinel handling |
| Fails on duplicates | Undefined duplicate policy, decide and document it |
| O(n²) in production, fast in tests | Test data was accidentally random; production data is sorted |

That last row is worth internalizing. Sorted input is the worst case for a naive BST and for quicksort with a fixed pivot, and real-world data arrives sorted far more often than random test data does: by timestamp, by ID, by insertion order. Test with sorted, reverse-sorted, and all-identical inputs deliberately.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**22.1 ★ Use the decision table.** For each requirement, pick a structure from the table in 22.1 and give the one-line reason. Say what you would *not* use.

1. A web crawler must skip URLs it has already fetched. It will see about 2 billion URLs, and occasionally skipping a page it has not fetched is acceptable.
2. A session store maps random session ids to user records. Nobody ever iterates it in order.
3. A trading system must answer "all orders placed between 10:00:00 and 10:05:00" while orders keep arriving.
4. A job scheduler repeatedly runs whichever pending job has the earliest deadline.
5. A service checks 30 feature flags by name on each request.

<details>
<summary>Solution</summary>

1. **Bloom filter.** Membership only, false positives allowed (a false positive means one skipped page). At about 10 bits per element, 2 billion URLs take about 2.5 GB. A hash set of the URL strings themselves would need well over 100 GB.
2. **Hash table.** Key to value with no ordering requirement is its exact job. A balanced tree would spend O(log n) comparisons and more memory to maintain an order nobody uses.
3. **Balanced BST or B-tree keyed by timestamp.** It is a range query, so the structure must keep keys ordered: find 10:00:00 in O(log n), then walk forward. A hash table cannot answer it without scanning everything.
4. **Binary heap keyed by deadline.** "Repeatedly extract the minimum" with inserts arriving is the heap's interface. A sorted array pays O(n) per insert.
5. **An array (or a plain dict), nothing clever.** At 30 items, constant factors dominate. A linear scan over 30 short strings is fast and fits in a few cache lines, and the "Under ~100 items" row applies. Either choice is fine; building anything elaborate is not.

</details>

**22.2 ★ The classic wrong BST checker.** 22.4 warns that a checker comparing each node only to its immediate children is wrong. Write that naive version, and give a tree it accepts that `check_bst` correctly rejects.

<details>
<summary>Solution</summary>

```python
class Node:
    def __init__(self, key, left=None, right=None):
        self.key, self.left, self.right = key, left, right

def check_bst(node, lo=float('-inf'), hi=float('inf')):
    if node is None:
        return True
    if not (lo < node.key < hi):
        return False
    return (check_bst(node.left, lo, node.key)
            and check_bst(node.right, node.key, hi))

def check_bst_naive(node):
    """WRONG: only compares parents with their own children."""
    if node is None:
        return True
    if node.left and not node.left.key < node.key:
        return False
    if node.right and not node.right.key > node.key:
        return False
    return check_bst_naive(node.left) and check_bst_naive(node.right)

#        10
#       /  \
#      5    20
#     / \
#    2   15      <- 15 is in 10's LEFT subtree but larger than 10
tree = Node(10, Node(5, Node(2), Node(15)), Node(20))
assert check_bst_naive(tree) is True
assert check_bst(tree) is False
```

Every parent-child pair is in order (2 < 5 < 15, 5 < 10 < 20), so the naive check passes. But 15 sits in the left subtree of 10, so a search for 15 goes right at the root and never finds it. The BST property constrains a node against *all* its ancestors, which is exactly what the `lo`/`hi` bounds carry down the recursion. When `check_bst` reaches 15, its window is (5, 10), and 15 falls outside it.

</details>

**22.3 ★★ An invariant checker for union-find.** 22.4 says that for union-find you should "check that no parent chain cycles". Write `check_union_find(parent)` for the array representation (`parent[i] == i` marks a root) that returns `True` exactly when every element's parent chain ends at a root and no parent index is out of range. It must run in O(n) total, not O(n) per element.

<details>
<summary>Hint</summary>

Mark nodes with three states: unvisited, on the walk you are doing right now, and already verified. Meeting a node from your own walk means a cycle; meeting a verified node means you can stop early.

</details>

<details>
<summary>Solution</summary>

```python
def check_union_find(parent):
    """True iff every parent chain ends at a root (parent[r] == r). O(n)."""
    n = len(parent)
    state = [0] * n                # 0 = unvisited, 1 = on current walk, 2 = verified
    for start in range(n):
        walk, x = [], start
        while state[x] == 0:
            state[x] = 1
            walk.append(x)
            p = parent[x]
            if not 0 <= p < n:
                return False       # parent points outside the structure
            if p == x:
                break              # reached a root
            x = p
        else:
            if state[x] == 1:
                return False       # came back to a node on this walk: a cycle
        for y in walk:
            state[y] = 2
    return True

assert check_union_find([0, 0, 1, 3, 3])        # two trees: {0,1,2} and {3,4}
assert check_union_find([])
assert not check_union_find([1, 2, 0, 3])       # 0 -> 1 -> 2 -> 0
assert not check_union_find([0, 2, 1])          # 1 <-> 2, never reaches root 0
assert not check_union_find([0, 5])             # out of range
```

Each walk stops at a root, at an already verified node, or at a cycle. Every node is marked 1 once and 2 once, and is never walked through again after being verified, so the total work is O(n) even though individual walks can be long. The `while ... else` clause runs only when the loop ends because it reached an already-visited node (not via `break`), which is exactly when that node might be on the current walk.

A naive version that walks the full chain from every element is O(n²) in the worst case (a single long chain), which would make "check after every operation" in a debug build painfully slow. If the structure also tracks set sizes for union by size, a natural extension checks that each root's stored size equals the number of elements whose chain ends there.

</details>

**22.4 ★★ Read the counters.** Two programs are profiled with `perf stat` as in 22.3:

| | instructions | cycles | cache-references | cache-misses |
|---|---|---|---|---|
| Program P | 3.2 × 10⁹ | 8.0 × 10⁹ | 2.0 × 10⁸ | 1.2 × 10⁸ |
| Program Q | 1.2 × 10¹⁰ | 4.8 × 10⁹ | 5.0 × 10⁷ | 1.0 × 10⁶ |

Compute IPC and the cache-miss rate for each. Which rung of the optimization ladder should each team try first, and what concretely would you look for?

<details>
<summary>Solution</summary>

| | IPC | Miss rate |
|---|---|---|
| P | 3.2 / 8.0 = **0.4** | 1.2 / 2.0 = **60%** |
| Q | 12 / 4.8 = **2.5** | 0.1 / 5 = **2%** |

**P is memory-bound.** An IPC of 0.4 means the core retires fewer than one instruction every two cycles, and 60% of cache references miss: the CPU is mostly waiting for data. Rung 2, memory layout. Look for pointer-chasing structures on the hot path (linked lists, a tree with one key per node, a hash table with chaining) and replace them with contiguous ones (arrays, B-tree-style wide nodes, open addressing), or shrink the hot struct so more of it fits per cache line. Tuning arithmetic will not help.

**Q is compute-bound.** IPC 2.5 with a 2% miss rate means data is arriving on time and the core is busy. Rung 1: look for an algorithmic improvement, such as work repeated inside a loop or a quadratic step that could be O(n log n). If the algorithm is already right, rung 5 (SIMD, branch elimination) is where the remaining speed is.

One caveat applies to both: rung 1 comes first if the algorithm is wrong. A quadratic algorithm can show either profile, and no layout fix will rescue it at large n.

</details>

**22.5 ★★ Why the tests were fast.** Count the comparisons a plain (unbalanced) BST makes when inserting the keys 0 to 999 in sorted order, and in a random order. Then explain why `test_matches_reference` in 22.4 is unlikely ever to exercise the slow case, and what to add so that it does.

<details>
<summary>Solution</summary>

```python
import random

class Node:
    def __init__(self, key):
        self.key, self.left, self.right = key, None, None

def count_comparisons(keys):
    root, comparisons = None, 0
    for k in keys:
        if root is None:
            root = Node(k)
            continue
        node = root
        while True:
            comparisons += 1
            if k < node.key:
                if node.left is None:
                    node.left = Node(k)
                    break
                node = node.left
            else:
                if node.right is None:
                    node.right = Node(k)
                    break
                node = node.right
    return comparisons

n = 1000
assert count_comparisons(range(n)) == n * (n - 1) // 2      # 499,500
shuffled = list(range(n))
random.shuffle(shuffled)
print(count_comparisons(shuffled))                          # about 11,000
```

**Sorted:** key k walks past all k earlier keys, so the total is 0 + 1 + ... + 999 = **499,500**. **Random:** about **11,000** on average (the expected value is 2(n+1)Hₙ − 4n ≈ 10,986, where Hₙ is the n-th harmonic number). Same code, a 45× difference at n = 1000, and the gap grows linearly with n.

`st.lists(st.integers())` generates lists of arbitrary integers in arbitrary order. A long list that happens to be sorted is vanishingly rare, so the property test checks correctness on near-random shapes and never builds a deep chain. The test is right to pass (the tree *is* correct on sorted input, just slow), which is why this bug class shows up only in production.

The fixes are deliberate. Generate the adversarial shapes 22.4 lists: `st.lists(st.integers()).map(sorted)`, the same mapped through `sorted(..., reverse=True)`, and lists of one repeated value. And add a *performance* property alongside the correctness one: for a structure that claims balance, assert that its height stays within its guaranteed bound (about 2 log₂ n for a red-black tree) after every operation. A height check turns "slow" into "failing", which a test can catch.

</details>

**22.6 ★★★ Find an LRU bug with a model-based test.** This LRU cache has a bug:

```python
class BuggyLRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}                       # Python dicts keep insertion order

    def get(self, key):
        return self.data.get(key)

    def put(self, key, value):
        if key in self.data:
            del self.data[key]
        elif len(self.data) == self.capacity:
            oldest = next(iter(self.data))
            del self.data[oldest]
        self.data[key] = value
```

Without reading the code for the bug, write the test 22.4 recommends: an obviously correct model built on `collections.OrderedDict`, random operation sequences, and a comparison after every `get`. Add a simple shrinker that removes operations while the failure persists. What minimal failing sequence does it find, what is the bug, and what is the fix?

<details>
<summary>Hint</summary>

Keep keys and capacity tiny (keys 0 to 4, capacity 1 to 3). Bugs in eviction logic need collisions, and a large key space makes them rare.

</details>

<details>
<summary>Solution</summary>

```python
import random
from collections import OrderedDict

class ModelLRU:
    """Obviously correct reference: slow is fine, wrong is not."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.d = OrderedDict()

    def get(self, key):
        if key not in self.d:
            return None
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.capacity:
            self.d.popitem(last=False)

def fails(make_impl, capacity, ops):
    impl, model = make_impl(capacity), ModelLRU(capacity)
    for op, key in ops:
        if op == "put":
            impl.put(key, key)
            model.put(key, key)
        elif impl.get(key) != model.get(key):
            return True
    return False

def find_failure(make_impl, trials=10_000, seed=0):
    rng = random.Random(seed)
    for _ in range(trials):
        capacity = rng.randint(1, 3)
        ops = [(rng.choice(["get", "put"]), rng.randint(0, 4))
               for _ in range(rng.randint(1, 12))]
        if fails(make_impl, capacity, ops):
            return capacity, ops
    return None

def shrink(make_impl, capacity, ops):
    """Greedily drop single operations while the sequence still fails."""
    changed = True
    while changed:
        changed = False
        for i in range(len(ops)):
            candidate = ops[:i] + ops[i + 1:]
            if fails(make_impl, capacity, candidate):
                ops, changed = candidate, True
                break
    return ops

capacity, ops = find_failure(BuggyLRU)
print(capacity, shrink(BuggyLRU, capacity, ops))
```

With this seed the shrunk failure is, at capacity 2:

```
put 0, put 3, get 0, put 4, get 0
```

The model: `get 0` makes 0 the most recently used, so `put 4` evicts 3, and the final `get 0` returns 0. The buggy cache returns `None`: it evicted 0. **`get` does not refresh recency**, so the cache evicts the least recently *inserted* key, which is FIFO, not LRU. Every test that only ever calls `put`, or calls `get` on keys that are never near eviction, passes.

The fix moves the key to the most-recent end on every hit:

```python
class FixedLRU(BuggyLRU):
    def get(self, key):
        if key not in self.data:
            return None
        value = self.data.pop(key)           # re-insert at the most-recent end
        self.data[key] = value
        return value

assert find_failure(FixedLRU) is None
assert find_failure(FixedLRU, trials=50_000, seed=7) is None
```

The model took ten lines and has no cleverness in it, which is the point: it is easy to trust. The shrinker is a crude version of what Hypothesis does automatically, and it turned an 11-operation random failure into 5 operations that explain the bug at a glance.

</details>

---

## Where this connects

- [Chapter 16: External Memory and Cache-Oblivious Structures](ch16-external-memory-and-cache-oblivious-structures.md). Why the profiler says memory and not arithmetic
- [Chapter 25: Complete Selection Guide and Complexity Reference](../volume-4/ch25-complete-selection-guide-and-complexity-reference.md). The selection matrix in reference form
