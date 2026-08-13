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

**Question 2 is the one people skip and shouldn't.** Sequential access and random access are different problems, and [Chapter 16](ch16-external-memory-and-cache-oblivious-structures.md) explains why the gap is 10–100×, not 10–20%. Ask specifically: do I ever need the elements *in order*? That single question separates hash tables from trees, and it is the most common source of a wrong initial choice — people reach for a hash map, then discover six months later that they need ordered iteration.

**Question 3 changes which model applies.** Under ~1,000 elements, constant factors dominate and a linear scan of an array frequently beats every "better" structure — it is one cache line at a time with perfect prefetching, and there is no hashing or pointer-chasing. Above what fits in RAM, the external memory model applies and B-trees or LSM trees are the only serious options.

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

**Question 5 deserves a warning.** "Is thread safety required?" is often answered too fast, in both directions. Wrapping every structure in a lock because the application is multithreaded is how you get a program that is slower than the single-threaded version. Conversely, a structure reachable from two threads without synchronization is broken even if it has never visibly failed. The best answer is usually to avoid sharing at all — see [Chapter 18](ch18-concurrent-data-structures.md).

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
| Python `list` | Dynamic array, ~1.125× growth | `insert(0, x)` is O(n) — use `collections.deque` |
| Java `HashMap` | Chaining; buckets become red-black trees past 8 entries | The treeification defends against collision DoS |
| Java `TreeMap` | Red-black tree | Sorted iteration, `floorKey`/`ceilingKey` |
| C++ `std::map` | Red-black tree | Ordered — `unordered_map` is the hash table |
| C++ `std::vector` | Dynamic array, typically 1.5–2× growth | `reserve()` when the size is known |
| C++ `std::list` | Doubly linked | Almost always the wrong choice; `vector` wins even for middle insertion at small n |
| Go `map` | Open addressing with 8-slot buckets | Iteration order is *deliberately randomized* |
| Rust `HashMap` | SwissTable (hashbrown), SipHash by default | Swap in `FxHash` for non-adversarial internal use |
| Rust `BTreeMap` | B-tree, not a BST | Cache-friendlier than a red-black tree |
| JS `Object` vs `Map` | Hidden classes vs real hash map | `Map` for dynamic keys; `Object` keys are strings/symbols |

Three practical notes that catch people repeatedly:

- **Go randomizes map iteration order on purpose**, so that code cannot come to depend on it. If you need order, sort the keys.
- **Rust's default hasher is SipHash**, chosen to resist collision attacks, and it is measurably slower than a non-cryptographic hash. For internal maps with trusted keys, `FxHashMap` is often 2× faster.
- **C++ `std::list` is nearly always a mistake.** The textbook case for a linked list — cheap insertion in the middle — loses to `std::vector` at surprisingly large n, because finding the insertion point requires a traversal and the traversal is cache-hostile. Measure before believing otherwise.

## 22.3 Performance Optimization

- **Profiling first**: Don't optimize without measuring
- **Cache awareness**: Sequential access > random access
- **Memory pools**: Reduce allocation overhead
- **Object pooling**: Reuse frequently allocated objects

**Profile first, and profile the right thing.** A wall-clock profiler tells you where time goes; it does not tell you *why*. If a function is slow and the arithmetic is trivial, the answer is usually memory, and you need hardware counters to see it:

```bash
perf stat -e cache-misses,cache-references,instructions,cycles ./program
```

An instructions-per-cycle figure below ~1.0 with a high cache-miss rate means the CPU is waiting on memory, and no amount of algorithmic micro-tuning will help — the layout is the problem. Above ~2.0 IPC, you are compute-bound and the algorithm is the thing to change. This single distinction redirects more optimization effort than any other measurement.

**The optimization ladder**, roughly in order of payoff per unit of effort:

1. **Better algorithm or structure.** O(n²) → O(n log n) beats every constant-factor trick combined. This is where the leverage is, and the rest of this book is about it.
2. **Better memory layout.** Struct-of-arrays over array-of-structs; contiguous over pointer-chasing; shrink the hot struct so more fits per cache line. Often 2–10×.
3. **Fewer allocations.** Pre-size containers (`reserve`, `make([]T, 0, n)`). Reuse buffers. Arena-allocate objects with a shared lifetime. Allocation is rarely the headline cost, but allocation *churn* wrecks locality and GC pause times.
4. **Batching.** Amortize per-operation overhead — one bulk insert instead of n inserts, one syscall instead of n.
5. **Micro-optimization.** Branch elimination, SIMD, intrinsics. Real, but last, and easily undone by the next compiler version.

**On object pooling specifically:** it is a genuine win for expensive-to-construct objects (database connections, threads, large buffers) and frequently a net loss for cheap ones in a garbage-collected language. Modern generational GCs allocate by bumping a pointer and collect short-lived objects nearly for free; a pool converts those into long-lived objects that survive into the old generation and must be traced on every major collection. Pool connections, not integers.

**On premature pessimization**, which is the more common error than premature optimization: choosing an O(n) structure where an O(1) one was equally convenient, copying a large object where a reference would do, or building a string in a loop with `+=`. None of these are "optimizations" to skip — they are defaults to get right the first time.

## 22.4 Debugging Data Structure Bugs

- **Invariants**: Check them during development
- **Visualization**: Draw the structure
- **Testing**: Property-based testing (QuickCheck)
- **Assertions**: Validate preconditions and postconditions

Data structure bugs have a characteristic signature: the structure is *silently* wrong long before anything visibly fails. A corrupted red-black tree keeps answering queries — it just answers some of them incorrectly, and the crash comes later, somewhere else. This is why the techniques below emphasize *detection near the cause* rather than debugging at the point of failure.

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

Note that `check_bst` must thread bounds down the recursion. The version that only compares each node to its immediate children is the classic wrong answer — it accepts trees that violate the BST property across subtrees.

Then run the checker after every mutation in debug builds:

```python
def insert(self, key):
    self._insert(key)
    assert self._check_invariants(), f"invariant broken inserting {key}"
```

This turns a bug that would surface a thousand operations later into one that surfaces on the operation that caused it. For a red-black tree, check all five properties; for a B-tree, check occupancy bounds and uniform leaf depth; for union-find, check that no parent chain cycles.

**Property-based testing is the highest-value testing technique for this domain**, because data structure correctness is naturally expressible as properties, and random generation finds the edge cases you did not think of — empty, single element, duplicates, exactly-at-capacity:

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

That first pattern — **model-based testing against a simple, obviously-correct reference implementation** — is the most effective single technique for validating a data structure. Your red-black tree should behave exactly like a sorted list; your LRU cache should behave exactly like an ordered dict with manual eviction. The reference can be absurdly slow; it only has to be right.

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

**For memory bugs** — use-after-free, double-free, buffer overruns in hand-written C structures — reach for the sanitizers rather than reasoning: `-fsanitize=address` and `-fsanitize=undefined` find in seconds what code review misses for weeks. For concurrent structures, `-fsanitize=thread`, Java's JCStress, or Rust's `loom` are effectively mandatory; a race that has not manifested in testing is not a race that does not exist.

**A checklist for the specific bug classes that recur:**

| Symptom | Usual cause |
|---------|-------------|
| Works until it doesn't, at a suspiciously round size | Resize/rehash logic |
| Wrong answer, no crash | Broken invariant — write the checker |
| Crash far from the real problem | Memory corruption — run ASan |
| Fails only under load | Race — run TSan |
| Fails only on the empty or single-element case | Missing base case; sentinel handling |
| Fails on duplicates | Undefined duplicate policy — decide and document it |
| O(n²) in production, fast in tests | Test data was accidentally random; production data is sorted |

That last row is worth internalizing. Sorted input is the worst case for a naive BST and for quicksort with a fixed pivot, and real-world data arrives sorted far more often than random test data does — by timestamp, by ID, by insertion order. Test with sorted, reverse-sorted, and all-identical inputs deliberately.
