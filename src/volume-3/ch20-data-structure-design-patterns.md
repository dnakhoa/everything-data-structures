# Chapter 20: Data Structure Design Patterns

The preceding chapters covered structures. This one covers the recurring shapes of the *code around* them: how to extend a structure without rewriting it, how to expose traversal without exposing internals, and how to keep the cost of an abstraction visible.

The patterns here are the Gang of Four patterns as they specifically apply to collections, plus a few that are particular to data structures and appear in no pattern catalog.

## 20.1 Wrapper/Decorator Pattern

Add functionality to existing structures:
```python
class SynchronizedDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def __getitem__(self, key):
        with self.lock:
            return super().__getitem__(key)
```

A decorator wraps a structure in another object with the same interface, adding behavior on the way through. Synchronization, logging, validation, caching, access counting, and copy-on-write are all naturally decorators. Each is a concern orthogonal to *how the data is stored*, so each belongs outside the storage.

The example above illustrates the pattern and also a trap worth naming, because it is the single most common way this pattern is misapplied. **Subclassing a built-in collection does not reliably intercept its operations.** `dict.update()`, `dict.get()`, and `dict.setdefault()` are implemented in C and do not route through `__getitem__`, so the lock above simply does not apply to them. The structure looks synchronized and is not.

Composition rather than inheritance fixes it, by making the delegation explicit:

```python
class SynchronizedDict:
    """Wraps a dict rather than subclassing it, so nothing bypasses the lock."""

    def __init__(self, initial=None):
        self._data = dict(initial or {})
        self._lock = threading.RLock()      # reentrant: safe if callbacks re-enter

    def __getitem__(self, key):
        with self._lock:
            return self._data[key]

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value

    def get(self, key, default=None):
        with self._lock:
            return self._data.get(key, default)
```

Worth being honest about what this buys: per-operation locking makes each operation atomic, but **sequences of operations still race**. `if k in d: d[k] += 1` acquires the lock twice and another thread can interleave between them. This is why Java deprecated `Hashtable` in favor of `ConcurrentHashMap`'s compound operations like `computeIfAbsent`, and why a synchronized wrapper is usually the wrong concurrency answer: see [Chapter 18](ch18-concurrent-data-structures.md).

Real uses: Java's `Collections.unmodifiableList()` and `synchronizedMap()`; Python's `types.MappingProxyType`; the copy-on-write wrappers in persistent collection libraries.

## 20.2 Composite Pattern

Tree-like hierarchical structures:
```python
class Component:
    def operation(self): pass

class Composite(Component):
    def __init__(self):
        self.children = []

    def add(self, c):
        self.children.append(c)

    def operation(self):
        for c in self.children:
            c.operation()
```

The composite pattern makes a leaf and a container of leaves interchangeable, so client code can treat "one thing" and "a tree of things" identically. Filesystems are the standard illustration. A directory's size is the sum of its children's sizes, and a file's size is its own, but the caller asks the same question of both:

```python
class Node(ABC):
    @abstractmethod
    def size(self) -> int: ...

class File(Node):
    def __init__(self, name, size):
        self.name, self._size = name, size

    def size(self):
        return self._size

class Directory(Node):
    def __init__(self, name):
        self.name, self.children = name, []

    def add(self, node: Node) -> "Directory":
        self.children.append(node)
        return self

    def size(self):
        return sum(child.size() for child in self.children)
```

This is exactly how the expression trees in [Chapter 6](../volume-1/ch06-tree-fundamentals-and-binary-trees.md) work: a literal and an operator node both answer `evaluate()`. It is also how the DOM, scene graphs, GUI widget hierarchies, and query plan trees are built.

**Two warnings.** First, recursive traversal means recursive depth. A deep composite will overflow the stack, and structures with user-controlled depth need an explicit stack instead. Second, the pattern is often written with `add()`/`remove()` on the base `Component` so leaves and composites share one interface; that forces leaves to implement operations that make no sense for them. Keeping child management on `Composite` alone is the safer choice, at the cost of clients needing a type check to add children.

## 20.3 Iterator Pattern

Abstract traversal:
```python
class TreeIterator:
    def __init__(self, root):
        self.stack = [root] if root else []

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stack:
            raise StopIteration
        node = self.stack.pop()
        if node.right:
            self.stack.append(node.right)
        if node.left:
            self.stack.append(node.left)
        return node.val
```

The iterator decouples *what you want to visit* from *how the structure is laid out*. Its real value is that it lets a caller consume a traversal without the structure handing over its internals, and without building an intermediate list.

The example above is a pre-order traversal made iterative: note the right child pushed before the left, so the left pops first. Doing this without recursion is not merely stylistic: it makes the traversal **lazy**, so a caller can stop early after examining three nodes of a million-node tree and pay for three.

In Python, generators express the same thing far more directly, and the in-order version is worth having since it is the traversal that yields a BST's keys in sorted order:

```python
def in_order(node):
    """Lazy in-order traversal. O(1) amortized per element, O(h) space."""
    stack, current = [], node
    while stack or current:
        while current:                 # descend left, remembering the path
            stack.append(current)
            current = current.left
        current = stack.pop()
        yield current.val              # visit
        current = current.right        # then the right subtree

# Consumes only as much of the tree as it needs:
first_five = list(itertools.islice(in_order(root), 5))
```

**Iterator invalidation** is the classic hazard: mutating a structure while iterating it. Removing from a Python list during a `for` loop skips elements; a C++ `vector` reallocation leaves every outstanding iterator dangling; Java throws `ConcurrentModificationException` from a modification counter checked on each `next()`. The three responses (undefined behavior, fail-fast, and snapshot semantics (`CopyOnWriteArrayList`))represent a real design choice, and fail-fast is usually the right one because it converts a silent wrong answer into a loud crash.

## 20.4 Builder Pattern

Complex construction:
```python
class BSTBuilder:
    def __init__(self):
        self.values = []

    def add(self, value):
        self.values.append(value)
        return self

    def build(self):
        self.values.sort()
        return self._build_range(0, len(self.values))

    def _build_range(self, lo, hi):
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        node = TreeNode(self.values[mid])
        node.left = self._build_range(lo, mid)
        node.right = self._build_range(mid + 1, hi)
        return node
```

Builders matter most for data structures when **bulk construction beats repeated insertion**, which is often, and by more than people expect.

The example is a good illustration of why. Inserting n sorted values into a plain BST one at a time produces a linked list of height n − 1. Collecting them, sorting once, and recursively taking the midpoint produces a perfectly balanced tree of height ⌊log₂ n⌋ in O(n log n) total, and needs no rotation logic at all.

The same asymmetry recurs throughout:

| Structure | Incremental | Bulk-loaded |
|-----------|------------|-------------|
| BST | O(n log n), possibly unbalanced | O(n) from sorted input, perfectly balanced |
| Binary heap | O(n log n) sift-ups | O(n) Floyd heapify |
| B-tree | O(n log n), ~70% node occupancy | O(n) sorted bulk load, ~100% occupancy |
| Hash table | O(n) with resizes along the way | O(n), pre-sized, no rehashing |
| R-tree | Poor structure, high overlap | Sort-Tile-Recursive packing, much better |
| Suffix array | n/a | O(n) with SA-IS |

The B-tree row is easy to overlook and matters in practice: incremental insertion leaves nodes about 70% full, so a bulk-loaded index is meaningfully smaller and shallower. This is exactly why `CREATE INDEX` on an existing table produces a better index than the same rows inserted one at a time, and why `REINDEX` is a real optimization.

One further note on the example: `build()` sorts `self.values` in place and can be called twice with different results if `add()` is called in between. Builders that are consumed by `build()` should say so, or copy.

## 20.5 Adapter, Flyweight, and Policy

Three more that earn their place in collection code.

**Adapter** converts one interface to another. A max-heap from a min-heap by negating keys is the smallest possible example, and Python's `heapq` (min-only)makes it a daily occurrence:

```python
class MaxHeap:
    """Adapts heapq's min-heap into a max-heap by negating."""
    def __init__(self):
        self._h = []

    def push(self, value):
        heapq.heappush(self._h, -value)

    def pop(self):
        return -heapq.heappop(self._h)
```

Also: a deque adapted to a stack or a queue, and a `Set` adapted from a `Map` with dummy values, which is literally how Java's `HashSet` is implemented.

**Flyweight** shares immutable state between many objects. String interning is the ubiquitous case: Java and Python both intern short strings so that a million occurrences of `"active"` cost one allocation. Tries share prefixes for the same reason, and the shared subtrees of persistent structures in [Chapter 17](ch17-persistent-data-structures.md) are flyweights created automatically by immutability.

**Policy / strategy** parameterizes a structure by a decision rather than baking it in. A comparator is the everyday example; so is a hash function, an eviction policy, or an allocator. C++'s `std::map<K, V, Compare, Allocator>` makes all of them template parameters, which is why the same container serves ascending order, descending order, and arena allocation with no runtime cost.

## 20.6 Choosing a Pattern

| Need | Pattern | Watch out for |
|------|---------|--------------|
| Add a cross-cutting concern | Decorator | Subclassing built-ins fails to intercept; per-op locks don't make sequences atomic |
| Uniform treatment of leaves and trees | Composite | Recursion depth; child ops on leaves |
| Expose traversal, hide layout | Iterator | Invalidation on mutation |
| Efficient construction | Builder | Bulk-load beats incremental more often than expected |
| Reconcile mismatched interfaces | Adapter | Thin wrappers can hide real cost |
| Many identical immutable values | Flyweight | Only helps if genuinely immutable |
| Vary one decision | Policy | Runtime polymorphism costs a virtual call |

**The pattern that applies to all of them:** an abstraction over a data structure hides the layout but does not hide the *cost*. A `List` interface backed by a linked list and one backed by an array have identical signatures and completely different performance, and code written against the interface will silently get whichever it is handed. This is the practical reason C++ names `std::vector` and `std::list` distinctly instead of offering one `List`, and the reason Java's `List` interface has been a recurring source of accidental O(n²) loops. `get(i)` in a loop over a `LinkedList` is quadratic and looks exactly like the linear version.

Abstract the interface. Document the cost.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**20.1 ★ Which calls take the lock?** Using the *first* `SynchronizedDict` in 20.1 (the one that subclasses `dict` and overrides only `__getitem__`), which of these operations acquire `self.lock`?

```python
d = SynchronizedDict(a=1)
d['a']
d.get('a')
'a' in d
d.setdefault('a', 0)
d['b'] = 2
for k in d:
    pass
```

How would you check your answer empirically rather than by reading CPython's source?

<details>
<summary>Solution</summary>

Only `d['a']`. `get`, `in` (`__contains__`), `setdefault`, and iteration are implemented in C on `dict` and never call the Python-level `__getitem__`. `d['b'] = 2` calls `__setitem__`, which the class does not override at all, so writes were never locked in the first place.

To check, replace the lock with a spy that records each call:

```python
calls = []

class Spy(dict):
    def __getitem__(self, key):
        calls.append(key)
        return super().__getitem__(key)

d = Spy(a=1)
d['a']
assert calls == ['a']
calls.clear()
d.get('a')
'a' in d
d.setdefault('a', 0)
for k in d:
    pass
assert calls == []          # none of these went through __getitem__
```

This is the trap 20.1 describes: the class looks synchronized because its one visible method is, while most of its interface bypasses that method.

</details>

**20.2 ★★ Make a compound operation atomic.** Assume the composition-based `SynchronizedDict` from 20.1 also has a locked `__contains__`. Two threads each run:

```python
if k in d:
    d[k] = d[k] + 1
else:
    d[k] = 1
```

Show an interleaving that loses an update. Then add a method to `SynchronizedDict` that makes this safe, and a general version that applies any function to a key's value atomically (in the spirit of Java's `compute`).

<details>
<summary>Hint</summary>

Each line is atomic on its own. The lock is released between the check and the act.

</details>

<details>
<summary>Solution</summary>

Starting with `k` absent: thread 1 evaluates `k in d` → False and releases the lock. Thread 2 evaluates `k in d` → False. Thread 1 sets `d[k] = 1`. Thread 2 sets `d[k] = 1`. Two increments, final value 1. The same happens with `k` present: both threads read `d[k] == 5`, both write 6.

The fix is to hold the lock across the whole read-modify-write, which only the class itself can do:

```python
import threading

class SynchronizedDict:
    def __init__(self, initial=None):
        self._data = dict(initial or {})
        self._lock = threading.RLock()

    def __getitem__(self, key):
        with self._lock:
            return self._data[key]

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value

    def __contains__(self, key):
        with self._lock:
            return key in self._data

    def increment(self, key, by=1):
        with self._lock:
            new = self._data.get(key, 0) + by
            self._data[key] = new
            return new

    def update_with(self, key, fn, default=None):
        """Atomically replace d[key] with fn(d.get(key, default))."""
        with self._lock:
            new = fn(self._data.get(key, default))
            self._data[key] = new
            return new

d = SynchronizedDict()

def work():
    for _ in range(20_000):
        d.increment('hits')

threads = [threading.Thread(target=work) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
assert d['hits'] == 80_000
assert d.update_with('log', lambda xs: (xs or []) + ['start']) == ['start']
```

`update_with` runs `fn` while holding the lock, which has a cost: a slow `fn` blocks every other caller, and the `RLock` is what makes it safe for `fn` to call back into `d`. Java's `ConcurrentHashMap.compute` has the same rule (keep the function short), for the same reason.

The general lesson: an atomic interface has to offer the compound operations its callers need. Locking each primitive separately cannot be composed into atomic sequences from outside.

</details>

**20.3 ★ Trace the iterators.** Use this BST with the `TreeIterator` and `in_order` code from 20.3:

```
        8
      /   \
     3     10
    / \      \
   1   6      14
      / \    /
     4   7  13
```

1. List the values `TreeIterator` yields, and the contents of its stack (bottom to top, as values) after each of the first three calls to `next()`.
2. List the values `in_order` yields.
3. `list(itertools.islice(in_order(root), 3))` returns three values. Which nodes have been pushed onto the generator's stack by then?

<details>
<summary>Solution</summary>

1. Pre-order: **8, 3, 1, 6, 4, 7, 10, 14, 13**.

| Call | Pops | Pushes (right first, then left) | Stack after | Yields |
|------|------|---------------------------------|-------------|--------|
| 1 | 8 | 10, 3 | [10, 3] | 8 |
| 2 | 3 | 6, 1 | [10, 6, 1] | 3 |
| 3 | 1 | nothing | [10, 6] | 1 |

2. In-order: **1, 3, 4, 6, 7, 8, 10, 13, 14**, the sorted keys.

3. The generator descends 8 → 3 → 1 (pushing all three), pops and yields 1, pops and yields 3, moves to 6 and descends 6 → 4 (pushing both), then pops and yields 4. Pushed so far: **8, 3, 1, 6, 4**, five of the nine nodes. Nodes 7, 10, 13, and 14 are never touched. That is the laziness 20.3 describes: the cost is proportional to what you consume plus the depth of the path to it.

</details>

**20.4 ★★ The height of a bulk-built tree.** Prove that `BSTBuilder._build_range` from 20.4 produces a tree of height exactly ⌊log₂ n⌋ for n ≥ 1 values (height counted in edges, as in Chapter 6). Then state the height for n = 10 and compare it with inserting the same 10 sorted values one at a time into a plain BST.

<details>
<summary>Hint</summary>

Work out the sizes of the left and right ranges when `mid = (lo + hi) // 2`, and use strong induction on n.

</details>

<details>
<summary>Solution</summary>

For a range of n values, `mid = lo + ⌊n/2⌋` (since `(lo + hi) // 2` with `hi = lo + n`), so the left range holds ⌊n/2⌋ values and the right range holds n − ⌊n/2⌋ − 1 = ⌈n/2⌉ − 1 values. The right range is never larger than the left.

Claim: h(n) = ⌊log₂ n⌋ for n ≥ 1, where an empty range contributes height −1.

- **Base:** n = 1 gives a single node, height 0 = ⌊log₂ 1⌋.
- **Step:** take n ≥ 2 and assume the claim for all smaller sizes. The left range has m = ⌊n/2⌋ ≥ 1 values, so its height is ⌊log₂ m⌋. The right range has at most m values, so by the hypothesis (or because it is empty) its height is at most ⌊log₂ m⌋. So h(n) = 1 + ⌊log₂ ⌊n/2⌋⌋. If 2ᵏ ≤ n < 2ᵏ⁺¹, then 2ᵏ⁻¹ ≤ ⌊n/2⌋ < 2ᵏ, so ⌊log₂ ⌊n/2⌋⌋ = k − 1 and h(n) = k = ⌊log₂ n⌋.

For n = 10: ⌊log₂ 10⌋ = **3**. Inserting the same 10 sorted values one at a time builds a chain of height **9**.

A quick empirical check:

```python
class TreeNode:
    def __init__(self, val):
        self.val, self.left, self.right = val, None, None

def build(values, lo, hi):
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = TreeNode(values[mid])
    node.left = build(values, lo, mid)
    node.right = build(values, mid + 1, hi)
    return node

def height(node):
    return -1 if node is None else 1 + max(height(node.left), height(node.right))

for n in range(1, 2000):
    assert height(build(list(range(n)), 0, n)) == n.bit_length() - 1   # floor(log2 n)
```

</details>

**20.5 ★★ The adapter's hidden assumption.** The `MaxHeap` adapter in 20.5 negates values. Name the inputs it cannot handle, and write a version that works for any values that support `<`, still built on `heapq`.

<details>
<summary>Solution</summary>

Negation only exists for numbers. Strings, tuples, dates, and most user-defined types raise `TypeError: bad operand type for unary -`. (Tuples of numbers could be negated field by field, but only by writing custom code per shape.)

The general fix inverts the *comparison* rather than the *value*, by wrapping each item:

```python
import heapq

class _Reversed:
    __slots__ = ("item",)

    def __init__(self, item):
        self.item = item

    def __lt__(self, other):
        return other.item < self.item       # reversed order

class MaxHeap:
    def __init__(self):
        self._h = []

    def push(self, item):
        heapq.heappush(self._h, _Reversed(item))

    def pop(self):
        return heapq.heappop(self._h).item

    def __len__(self):
        return len(self._h)

h = MaxHeap()
for word in ["pear", "apple", "fig", "kiwi"]:
    h.push(word)
assert [h.pop() for _ in range(4)] == ["pear", "kiwi", "fig", "apple"]
```

`heapq` only uses `<`, so defining `__lt__` is enough. This is still an adapter, one layer deeper: the wrapper adapts each item's ordering, and `MaxHeap` adapts the heap's interface. It costs an object allocation and a Python-level method call per comparison, so for plain numbers the negation version is faster. That is the "thin wrappers can hide real cost" row of the 20.6 table.

</details>

**20.6 ★★ An accidental quadratic.** Here is a linked list that supports indexing, and two ways to sum a sequence:

```python
class LinkedList:
    class _Node:
        __slots__ = ("val", "next")

        def __init__(self, val, nxt):
            self.val, self.next = val, nxt

    def __init__(self, items):
        self.head, self.n, self.hops = None, 0, 0
        for x in reversed(items):
            self.head = self._Node(x, self.head)
            self.n += 1

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        if not 0 <= i < self.n:
            raise IndexError(i)
        node = self.head
        for _ in range(i):
            node = node.next
            self.hops += 1
        return node.val

    def __iter__(self):
        node = self.head
        while node:
            yield node.val
            node = node.next

def total_by_index(seq):
    t = 0
    for i in range(len(seq)):
        t += seq[i]
    return t

def total_by_iter(seq):
    t = 0
    for x in seq:
        t += x
    return t
```

For a 1,000-element list, how many `hops` does `total_by_index` cost? What is the general formula and complexity? What does `total_by_iter` cost? What would change if `__getitem__` walked from whichever end is closer, as Java's `LinkedList.get` does?

<details>
<summary>Solution</summary>

`seq[i]` walks i links, so the total is 0 + 1 + ... + (n − 1) = n(n − 1)/2. For n = 1000 that is **499,500 hops**: Θ(n²). `total_by_iter` follows each link once, n steps in total: Θ(n).

```python
L = LinkedList(list(range(1000)))
assert total_by_index(L) == 499_500 and L.hops == 499_500
L.hops = 0
assert total_by_iter(L) == 499_500 and L.hops == 0     # iteration never calls __getitem__
```

Walking from the nearer end makes `get(i)` cost min(i, n − 1 − i), which roughly halves the total to about n²/4. Still quadratic.

Both functions have the same signature and both are correct for any sequence. Handed a Python `list`, they are equally fast; handed this linked list, one is 500 times slower at n = 1000 and the gap grows linearly with n. This is the closing point of 20.6: the interface hid the layout, and the layout decided the cost. The fix is to write traversals with iteration, which every sequence can do at its own best speed, and to reserve `seq[i]` for structures that document O(1) indexing.

</details>

**20.7 ★★★ A fail-fast iterator.** Implement a small `DynamicArray` (wrapping a Python list is fine) whose iterator raises `RuntimeError` if the array is structurally modified (an element added or removed) during iteration, using a modification counter as Java does. Replacing an element in place should *not* count as a structural modification. Make sure a modification made while processing the *last* element is also caught.

<details>
<summary>Hint</summary>

The iterator records the counter when it starts and compares on every step. Think about where the last comparison happens when the loop body modifies the array after the final `yield`.

</details>

<details>
<summary>Solution</summary>

```python
class DynamicArray:
    def __init__(self):
        self._items = []
        self._mods = 0                  # bumped by every structural change

    def append(self, x):
        self._items.append(x)
        self._mods += 1

    def pop(self):
        self._mods += 1
        return self._items.pop()

    def __setitem__(self, i, x):
        self._items[i] = x              # replacing a value is not structural

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        expected = self._mods
        for i in range(len(self._items)):
            if self._mods != expected:
                raise RuntimeError("DynamicArray modified during iteration")
            yield self._items[i]
        if self._mods != expected:      # catches a change made after the last yield
            raise RuntimeError("DynamicArray modified during iteration")

a = DynamicArray()
for x in [1, 2, 3]:
    a.append(x)
for i, x in enumerate(a):
    a[i] = x * 10                       # allowed
assert list(a) == [10, 20, 30]

for trigger, mutate in [(20, lambda: a.append(99)), (99, a.pop)]:
    try:
        for x in a:
            if x == trigger:
                mutate()
        raise AssertionError("mutation was not detected")
    except RuntimeError:
        pass
assert list(a) == [10, 20, 30]
```

The first case appends 99 mid-iteration and is caught on the next step. That leaves 99 as the last element, so the second case pops it while processing the last element. Without the final check after the loop, that pop would go unnoticed: the generator would simply finish.

Why in-place replacement is exempt: it cannot make the iterator skip, repeat, or read out of bounds, because positions and length are unchanged. Java's `ArrayList.set` does not bump `modCount` for the same reason.

The check is "best effort" in the same sense as Java's: it detects modifications made through the array's own methods, on the iterating thread. It is a debugging aid that turns the silent skipped-element bug from 20.3 into a loud error, not a concurrency control.

</details>

---

## Where this connects

- [Chapter 22: Practical Considerations](ch22-practical-considerations.md). The practical judgment these patterns support
- [Chapter 6: Tree Fundamentals and Binary Trees](../volume-1/ch06-tree-fundamentals-and-binary-trees.md). The composite and iterator patterns in their original setting
