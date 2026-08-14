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

**Iterator invalidation** is the classic hazard: mutating a structure while iterating it. Growing a Python list during a `for` loop skips elements; a C++ `vector` reallocation leaves every outstanding iterator dangling; Java throws `ConcurrentModificationException` from a modification counter checked on each `next()`. The three responses (undefined behavior, fail-fast, and snapshot semantics (`CopyOnWriteArrayList`))represent a real design choice, and fail-fast is usually the right one because it converts a silent wrong answer into a loud crash.

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

The example is a good illustration of why. Inserting n sorted values into a plain BST one at a time produces a linked list of height n. Collecting them, sorting once, and recursively taking the midpoint produces a perfectly balanced tree of height ⌈log₂ n⌉ in O(n log n) total, and needs no rotation logic at all.

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

---

## Where this connects

- [Chapter 22: Practical Considerations](ch22-practical-considerations.md). The practical judgment these patterns support
- [Chapter 6: Tree Fundamentals and Binary Trees](../volume-1/ch06-tree-fundamentals-and-binary-trees.md). The composite and iterator patterns in their original setting
