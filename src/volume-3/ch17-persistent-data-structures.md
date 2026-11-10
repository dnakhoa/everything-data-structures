# Chapter 17: Persistent Data Structures

## 17.1 Persistence Defined

A persistent data structure preserves previous versions when modified.

**Types:**
- **Partial persistence**: Query old versions, update current
- **Full persistence**: Query and update any version
- **Confluent persistence**: Merge versions

Every structure so far has been **ephemeral**: modifying it destroys what was there before. Insert into a BST and the old tree is gone. Persistence removes that destruction. An update returns a *new* version while every old version remains valid and queryable.

The naive implementation is to copy the whole structure on every update, which is correct, obvious, and O(n) per operation in both time and space. The entire subject is about achieving persistence without paying that price. The key insight is that an update usually touches a small part of the structure, so the new version can **share** everything it did not touch with the old one.

The three levels of persistence form a strict hierarchy:

| Level | Query | Update | Version structure |
|-------|-------|--------|-------------------|
| Partial | Any version | Newest only | A line |
| Full | Any version | Any version | A tree |
| Confluent | Any version | Any version, plus merge | A DAG |

Confluent persistence is genuinely harder than the other two. When versions can merge, a node can be reachable by exponentially many paths, and the naive analysis of sharing breaks down.

**Immutability is the enabling property.** Sharing is only safe if shared nodes are never modified in place. Otherwise a change made through the new version would be visible through the old one, which is exactly what persistence is supposed to prevent. This is why persistent structures and functional programming arrived together.

## 17.2 Persistent BSTs

<figure>
{{#include ../images/path-copying.svg}}
<figcaption>Path copying: only the root-to-insertion path is duplicated.</figcaption>
</figure>

Share unchanged nodes on modification. Inserting 35 requires copying every node on the path from the root down to the insertion point, and only those nodes. Everything hanging off that path is shared with the previous version:

```
Before (version 1):        After (version 2), inserting 35:

      A(50)                  A(50)          A'(50)      ← new root
     /     \                /     \        /      \
  B(30)   C(70)          B(30)   C(70)  B'(30)     │
   /                      /               /   \     │
D(10)                  D(10)          D(10)  E(35)  │
                          ↑              ↑     ↑     │
                          └──────────────┘     │     │
                              shared        new    shared
                                            node   (C(70))

Version 1 root = A, version 2 root = A'.
Copied: A → A', B → B'.  New: E(35).  Shared: D(10), C(70).
```

Note that **B must be copied, not shared**: its right-child pointer changes to point at the new node E. This is the part that is easy to get wrong. Any node whose pointers change must be copied; a node is only shareable if nothing about it changes. Since only nodes along the root-to-leaf path have changed children, exactly O(log n) nodes are copied in a balanced tree.

```python
def insert(node, key):
    """Returns the root of a NEW version; `node` remains valid and unchanged."""
    if node is None:
        return Node(key, None, None)
    if key < node.key:
        return Node(node.key, insert(node.left, key), node.right)   # copy, new left
    elif key > node.key:
        return Node(node.key, node.left, insert(node.right, key))   # copy, new right
    return node                                                      # already present

v1 = build_tree([50, 30, 70, 10])
v2 = insert(v1, 35)     # v1 still queryable, unchanged
v3 = insert(v2, 60)     # three coexisting versions
```

There is no mutation anywhere in that function (it only ever constructs new nodes) which is what makes the old roots remain valid.

**This is path copying**, and its cost is the height of the tree:

| Operation | Time | Extra space per version |
|-----------|------|------------------------|
| Insert / delete (balanced) | O(log n) | O(log n) |
| Query any version | O(log n) | n/a |
| Insert (unbalanced worst case) | O(n) | O(n) |

Balance matters more here than in the ephemeral case, because an unbalanced tree costs you both time *and* permanent space on every update. Red-black trees and AVL trees both path-copy cleanly; the rotations simply produce a few more copied nodes.

Path copying is not the only technique. Section 17.3 covers the two alternatives, fat nodes and node copying, which avoid copying the path at all.

## 17.3 Fat Nodes and Node Copying

Path copying pays for the whole root-to-leaf path because of a cascade: a changed pointer forces a copy of the node holding it, which changes a pointer in *its* parent, and so on up to the root. Driscoll, Sarnak, Sleator and Tarjan ("Making Data Structures Persistent", STOC 1986; journal version 1989) asked the general question. Take any ephemeral pointer structure, where an update is a sequence of **update steps** (each writes one field of one node) and a query is a sequence of **access steps** (each reads one field). How cheaply can it be made persistent? They gave two answers, both of which stop the cascade at the first node.

### Fat nodes

Never overwrite a field. Each field keeps its whole history as a list of (version, value) pairs. A write in version v appends (v, value); a read in version v takes the latest entry stamped ≤ v. Under partial persistence versions are numbered 1, 2, 3, ... and writes only go to the newest version, so each history is sorted by construction and a read is a binary search.

```python
from bisect import bisect_right

class FatNode:
    """A BST node whose child fields keep their whole history."""
    def __init__(self, key):
        self.key = key                     # never changes
        self.left = ([0], [None])          # (version stamps, values), stamps ascending
        self.right = ([0], [None])

def read(field, v):
    stamps, values = field
    return values[bisect_right(stamps, v) - 1]   # last write stamped <= v: O(log m)

def write(field, v, value):
    stamps, values = field
    stamps.append(v)                       # v is the newest version, so order holds
    values.append(value)

class FatBST:
    """Partially persistent BST: query any version, insert into the newest."""
    def __init__(self):
        self.roots = [None]                # roots[v] is the root of version v

    def insert(self, key):
        v = len(self.roots)                # the version this insert creates
        root = self.roots[-1]
        self.roots.append(root if root is not None else FatNode(key))
        node = root
        while node is not None and node.key != key:
            field = node.left if key < node.key else node.right
            child = read(field, v)
            if child is None:
                write(field, v, FatNode(key))   # the only change: one field entry
            node = child
        return v

    def contains(self, key, v):
        node = self.roots[v]
        while node is not None and node.key != key:
            node = read(node.left if key < node.key else node.right, v)
        return node is not None

t = FatBST()
for k in [50, 30, 70, 10, 35]:
    t.insert(k)                            # versions 1 to 5
assert t.contains(35, 5) and not t.contains(35, 4)
assert t.contains(10, 4) and not t.contains(10, 3)
```

Trace the same keys as Section 17.2. Each insert allocates one node and appends one entry to one field: version 4 writes B(30)'s `left`, version 5 writes B(30)'s `right`. After version 5, B's `right` field holds stamps `[0, 5]` and values `[None, E(35)]`. The query `contains(35, 4)` reaches B and reads `right` at version 4: `bisect_right([0, 5], 4) - 1 = 0`, so it sees `None` and reports 35 absent. At version 5 the index is 1 and it finds E. Nothing was copied; A, B, C and D are the same objects in every version.

The bounds: **O(1) worst-case space per update step** (one appended pair), and an **O(log m) slowdown per access step**, where m is the number of writes to that field. A search of depth d in an old version costs O(d log m) rather than O(d). For full persistence the versions form a tree, so "latest version ≤ v" needs an order on that tree. DSST keep the versions in an order-maintenance list (a linear order consistent with the version tree, comparable in O(1)) and store each field's history in a search tree under that order. The space stays O(1) per update step and the slowdown O(log m).

### Node copying

Node copying keeps the O(1) space and removes the log factor, for partial persistence of structures with **bounded in-degree**: no node is pointed to by more than p nodes, for a constant p. A binary tree with parent pointers qualifies with p = 3 (a parent and two children point at each node).

Each node keeps the field values it was created with, plus a fixed number of **modification slots**, 2p of them, each holding (version, field, value). It also keeps up to p **back pointers** to the nodes that point at it in the newest version; those are only ever needed for the newest version, so they are overwritten in place.

- **Read** field f in version v: take the creation value, overridden by the latest slot for f stamped ≤ v. There are at most 2p slots, so this is O(1) worst case.
- **Write** field f in the newest version v: if the node has a free slot, fill it. If all 2p are full, make a **copy** holding the newest value of every field (with this write applied) and no slots in use. Each of the at most p nodes that point at the old node, found through its back pointers, must now point at the copy in version v, and the copy's children get their back pointers redirected to it. Redirecting a predecessor is a write to *its* field, done by this same procedure, so it may fill a slot or cascade into another copy. If the copied node was the root, the copy becomes version v's root.

The cascade can run far, but it cannot run often. Let c be the cost of copying a node (a constant, since nodes have bounded size) and let the potential be Φ = c × (number of filled slots in nodes of the newest version). Claim: every write has amortized cost at most 2c.

- **Free slot:** actual cost at most c, and Φ rises by c. Amortized: at most 2c.
- **Full node:** the copy costs c. The old node leaves the newest version and takes its 2p filled slots with it, so Φ falls by 2pc; the copy starts with none. Then come at most p recursive writes, each amortized at most 2c by induction. Amortized: at most c − 2pc + p · 2c = c.

So each update step costs **O(1) amortized time and space** (copies are the only space beyond the slots), and each access step costs **O(1) worst case**: no slowdown at all. This is the headline DSST result: any pointer structure with bounded in-degree can be made partially persistent with O(1) amortized overhead per update step and O(1) per access step. Their **node splitting** method extends it to full persistence with the same amortized bounds.

A red-black tree insertion performs O(1) amortized update steps (at most two rotations and O(1) amortized recolorings), so a node-copying persistent red-black tree costs O(1) amortized space per insertion, against O(log n) for path copying. Sarnak and Tarjan used exactly this for **planar point location**. Sweep a vertical line across a planar subdivision with n edges, keeping the edges that cross the line in a persistent search tree; each vertex the sweep passes creates a new version. That is O(n) space in total, and a query takes O(log n): binary-search the x-coordinate to pick the version, then search that version's tree by y.

### Comparing the three

| | Path copying | Fat nodes | Node copying |
|---|---|---|---|
| Space per update | Length of the path: O(log n) in a balanced tree | O(1) worst case per update step | O(1) amortized per update step |
| Time per access step | O(1) | O(log m) | O(1) |
| Old versions' nodes | Never touched | Histories grow in place | Slots filled in place |
| Purely functional | Yes | No | No |
| Level | Full | Partial; full with an ordered version list | Partial; full by node splitting |
| Restriction | No parent or back pointers | None | Bounded in-degree |

The restriction on path copying is real: if children point back at their parent, copying a node forces a copy of each child (its parent pointer must now lead to the copy), then of their children, and the copying spreads to the whole structure. That is why persistent trees in functional languages have no parent pointers.

Path copying still wins in practice, for reasons the asymptotics do not show. It never writes to memory an old version can see, so readers of old versions need no synchronization (the property Section 17.7 builds on) and it works in languages with no mutation at all. A version nobody references can be reclaimed by the garbage collector, while fat nodes and node copying embed every version's history inside nodes that stay live. And it is a few lines of code. Fat nodes and node copying are the theory's answer, and the right tool when space per update is what matters, as in the point-location sweep. Chapter 24 (Section 24.9) sketches a fat-node modification log at the research level.

## 17.4 Persistent Arrays and HAMTs

Trees path-copy naturally because they are already logarithmic-depth pointer structures. Arrays do not. A persistent array cannot copy 1,000,000 elements per write.

The standard solution is to stop using a flat array and use a **wide, shallow tree** instead, then path-copy that. Clojure's persistent vector is a 32-way branching trie: with a branching factor of 32, a vector of a billion elements is only 6 levels deep, so an update copies 6 nodes of 32 pointers each rather than a billion elements. Depth is ⌈log₃₂ n⌉, which for any realistic n is at most 7. Close enough to constant that these are often described as "effectively O(1)" operations.

```
32-way trie holding 1,000,000 elements, 4 levels deep:

              [root: 32 ptrs]
             /       |       \
        [32 ptrs] [32 ptrs] [32 ptrs]     ← copied only along the path
        /    |         |          \
     ...   [32 ptrs]  ...        ...
              |
        [32 values]  ← leaf: the element lives here

Update one element: copy 4 nodes (~128 pointers), share everything else.
```

### Inside the persistent vector

Three design decisions make this work in Clojure's `PersistentVector`, and Scala's immutable `Vector` uses the same 32-way radix layout.

**Bit-partitioned indexing.** Nodes have 2^b children (b = 5 gives 32), and every leaf except the last is full, so an index *is* a path. Read it b bits at a time from the top: in a three-level trie, index 13,399 = `01101 00010 10111` in binary goes to slot 13 of the root, slot 2 of the next node, and slot 23 of the leaf. Each level is a shift and a mask, `(i >> level) & 31`, with no comparisons and no keys stored.

**Path copying.** `set(i, x)` rebuilds the one node per level on that path and shares every other child pointer.

**The tail.** The last partial leaf (up to 32 elements) is kept outside the trie, in a separate `tail` array. An append that fits copies only the tail. Only every 32nd append pushes the full tail into the trie as a new leaf, path-copying O(log₃₂ n) nodes, and when the trie is completely full the root grows a level. The last elements, which stack-like code reads most, are found without entering the trie at all.

Here is a small version with the branching factor as a parameter. Nodes are tuples, so nothing is modified in place:

```python
class PVector:
    """Bit-partitioned persistent vector (Clojure's design) with 2**bits-way nodes.
    The last, possibly partial, leaf lives in `tail`, outside the trie."""

    def __init__(self, bits=5, count=0, shift=None, root=(), tail=()):
        self.bits, self.width, self.mask = bits, 1 << bits, (1 << bits) - 1
        self.count, self.root, self.tail = count, root, tail
        self.shift = bits if shift is None else shift   # index bits above the leaf level

    def _new(self, count, shift, root, tail):
        return PVector(self.bits, count, shift, root, tail)

    def _tail_offset(self):                    # index of tail[0]
        if self.count < self.width:
            return 0
        return ((self.count - 1) >> self.bits) << self.bits

    def __len__(self):
        return self.count

    def __getitem__(self, i):
        if not 0 <= i < self.count:
            raise IndexError(i)
        if i >= self._tail_offset():
            return self.tail[i - self._tail_offset()]
        node = self.root
        for level in range(self.shift, 0, -self.bits):  # one chunk of bits per level
            node = node[(i >> level) & self.mask]
        return node[i & self.mask]

    def set(self, i, x):
        if not 0 <= i < self.count:
            raise IndexError(i)
        off = self._tail_offset()
        if i >= off:
            t = self.tail
            return self._new(self.count, self.shift, self.root,
                             t[:i - off] + (x,) + t[i - off + 1:])
        def assoc(node, level):                # path copying: one new node per level
            j = (i >> level) & self.mask
            child = x if level == 0 else assoc(node[j], level - self.bits)
            return node[:j] + (child,) + node[j + 1:]
        return self._new(self.count, self.shift, assoc(self.root, self.shift), self.tail)

    def append(self, x):
        if len(self.tail) < self.width:        # common case: copy only the tail
            return self._new(self.count + 1, self.shift, self.root, self.tail + (x,))
        # The tail is full: it becomes a leaf of the trie, and x starts a new tail.
        if (self.count >> self.bits) > (1 << self.shift):   # no room: grow a level
            root = (self.root, self._path(self.shift, self.tail))
            return self._new(self.count + 1, self.shift + self.bits, root, (x,))
        return self._new(self.count + 1, self.shift,
                         self._push_tail(self.shift, self.root), (x,))

    def _path(self, level, leaf):              # fresh chain of one-child nodes
        return leaf if level == 0 else (self._path(level - self.bits, leaf),)

    def _push_tail(self, level, node):
        j = ((self.count - 1) >> level) & self.mask    # slot on the path to the new leaf
        if level == self.bits:
            child = self.tail
        elif j < len(node):
            child = self._push_tail(level - self.bits, node[j])
        else:
            child = self._path(level - self.bits, self.tail)
        return node[:j] + (child,) + node[j + 1:]
```

The overflow test reads: after this push the trie holds `count >> bits` full leaves, and a trie whose root sits `shift` bits above the leaves has room for 2^shift of them.

With 4-way nodes (`bits=2`) the trie gets deep quickly, which makes the structure easy to see. Appending 0, 10, ..., 200 gives 21 elements:

```
shift = 4, tail = (200,), tail offset 20
root ─┬─ [0] ─┬─ (0, 10, 20, 30)          indices  0..3
      │       ├─ (40, 50, 60, 70)                  4..7
      │       ├─ (80, 90, 100, 110)                8..11
      │       └─ (120, 130, 140, 150)             12..15
      └─ [1] ─── (160, 170, 180, 190)             16..19
```

The 21st append is the one that grew the root. Its tail (160 to 190) was full, the trie already held 4 leaves (= 2^2, full for `shift = 2`), so 20 >> 2 = 5 > 4: the old root became child 0 of a new root and a one-child path to the new leaf became child 1. Looking up index 13 = `00 11 01` takes slot 0, then slot 3, then slot 1: the value 130. `set(13, -1)` copies the root, node [0] and leaf 3, three tuples, and shares the other three leaves, node [1] and the tail:

```python
v = PVector(bits=2)                   # 4-way nodes, so the trie gets deep fast
for i in range(21):
    v = v.append(i * 10)
assert (v.shift, v.tail, len(v)) == (4, (200,), 21)
assert v[13] == 130                   # 13 = 0b00_11_01: slots 0, 3, 1
w = v.set(13, -1)
assert v[13] == 130 and w[13] == -1   # v is untouched
assert w.root[1] is v.root[1] and w.root[0][0] is v.root[0][0]   # shared, not copied
```

**What "effectively constant" means.** Lookup and update cost Θ(log₃₂ n) = Θ(log₂ n / 5). That is a constant factor of 5 fewer levels than a binary tree, not a different growth rate. The claim of "effectively O(1)" rests on the fact that n is bounded in practice: with 32-bit indices there are at most 7 levels (32 bits in 5-bit chunks), and by the same logic a balanced binary tree is "effectively at most 32 levels". The concrete costs are what matter. A lookup is up to 7 dependent pointer loads where an array needs one (the top levels usually sit in cache, the lower ones often do not). An update allocates up to 7 nodes of 32 slots, a couple of hundred words, where an array writes one. Clojure and Scala offer **transient** vectors and builders for bulk construction, which mutate nodes that no other version can see yet and then freeze the result.

The design has one hard limit: the index arithmetic requires every leaf except the last to be full, so concatenating two vectors means re-appending one of them element by element, O(n), and a real slice from the middle has to be rebuilt the same way. (Clojure's `subvec` is O(1) only because it returns a view that keeps the whole original alive.) **RRB trees** (relaxed radix balanced trees) allow some nodes to be less than full and store a small table of subtree sizes in those nodes, which gives O(log n) concatenation and splitting while keeping radix lookup on the full parts.

The **Hash Array Mapped Trie (HAMT)** applies the same structure to maps. Hash the key, then use 5 bits of the hash per level to index into a 32-wide node. The refinement that makes it space-efficient is a bitmap in each node marking which of the 32 slots are occupied, so a node with 3 children stores 3 pointers and a 32-bit mask rather than 32 mostly-null pointers. Population count on the bitmap converts a logical index to a physical one in one instruction.

HAMTs are the backbone of persistent maps in Clojure, Scala, and Haskell, and the same idea appears in Erlang and in immutable-collections libraries for JavaScript.

## 17.5 Persistent Queues: Amortization Meets Persistence

The functional queue is the two-stack queue of Exercise 5.5 ([Chapter 5](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md)) built from immutable lists: a front list F, a rear list R holding the newest element first, enqueue conses onto R, dequeue takes from F, and when F runs out R is reversed to become the new F. Every element is reversed once, so n operations cost O(n): amortized O(1). Exercise 17.6 runs the experiment that breaks it. Take a version whose F is empty and whose R holds n elements, and call dequeue on that same version n times. Every call reverses all n elements and returns the result inside a new version that the caller throws away: n² work for n operations.

The analysis failed because it is a **credit** argument. Each cheap enqueue puts a coin in the bank, and the expensive reversal spends the coins. Under persistence a version has many futures, and every future spends the same coins. No credit argument survives that, because the same savings can be withdrawn any number of times.

### Debits instead of credits

Okasaki's repair turns the accounting around and changes the code to match. It has two ingredients.

1. **Lazy evaluation with memoization.** The rotation is not performed. It is stored in the new version as a **suspension**, a thunk that runs the first time anyone needs its result and caches the answer. Every version derived from that one shares the same suspension object, so the work runs at most once, however many futures reach it.
2. **Schedule the expensive work early.** Rotate as soon as R would become longer than F, building `F ++ reverse(R)` lazily. The invariant |R| ≤ |F| puts the reversed part behind |F| elements, so on any path through the version tree, |F| dequeues must happen before anything can force it.

The accounting uses **debits**. When a suspension is created, its cost is recorded as a debt against it, and the rule is that it may only be forced after earlier operations have paid that debt off. If two futures each do their |F| dequeues, the debt is paid twice, which is harmless overpayment; memoization guarantees the real cost is incurred only once. Credits can be double-spent; debits can only be double-paid. That asymmetry is the whole idea.

For this **banker's queue** the bookkeeping is concrete. Number the cells of F from 0 and let D(i) be the total debt on cells 0 through i. The invariant is

> D(i) ≤ min(2i, |F| − |R|)

- Cell 0 always carries zero debt, so the dequeue that forces it is allowed.
- An enqueue that does not rotate lowers |F| − |R| by one, so it pays off 1 debit.
- A dequeue moves every cell one place forward (lowering 2i by 2) and lowers |F| − |R| by one, so it pays off 2 debits.
- A rotation happens when |R| reaches |F| + 1, with |F| = m. Just before that enqueue, |F| = |R| = m, so the invariant forced every D(i) to 0: the old front was fully paid for. The rotation puts 1 debit on each of the first m cells (each step of the lazy append is a small suspension) and m + 1 on cell m (the reversal), so D(i) = i + 1 for i < m and D(m) = 2m + 1. The enqueue pays the debit on cell 0, leaving D(i) = i ≤ 2i and D(m) = 2m ≤ min(2m, 2m + 1). The invariant holds again.

Every operation does O(1) unshared work and pays at most 2 debits, so the banker's queue is **O(1) amortized per operation, under any pattern of persistent use**.

Python is strict, so laziness has to be simulated. A `Susp` holds a thunk and memoizes it, and a stream is a `Susp` whose value is `None` or a `(head, stream)` pair:

```python
class Susp:
    """A memoized thunk: the computation runs at most once, ever."""
    def __init__(self, thunk):
        self.thunk, self.value = thunk, None

    def force(self):
        if self.thunk is not None:
            self.value, self.thunk = self.thunk(), None
        return self.value

def ready(cell):
    """A stream cell that is already evaluated."""
    s = Susp(None)
    s.value = cell
    return s

EMPTY = ready(None)   # a stream is a Susp whose value is None or (head, stream)
steps = 0             # counts reversal work, for the experiments below

def append(s, t):
    """Lazy s ++ t: each cell costs O(1), paid only when that cell is forced."""
    def cell():
        c = s.force()
        return t.force() if c is None else (c[0], append(c[1], t))
    return Susp(cell)

def reverse(lst):
    """Lazy but monolithic: the first force reverses the whole cons list."""
    def run():
        global steps
        out, rest = EMPTY, lst
        while rest is not None:
            steps += 1
            out, rest = ready((rest[0], out)), rest[1]
        return out.force()
    return Susp(run)

# A banker's queue is (len_f, front stream, len_r, rear cons list), len_r <= len_f.
EMPTY_Q = (0, EMPTY, 0, None)

def check(lf, f, lr, r):
    if lr <= lf:
        return (lf, f, lr, r)
    return (lf + lr, append(f, reverse(r)), 0, None)   # rotate early, lazily

def enqueue(q, x):
    lf, f, lr, r = q
    return check(lf, f, lr + 1, (x, r))

def dequeue(q):
    lf, f, lr, r = q
    x, rest = f.force()
    return x, check(lf - 1, rest, lr, r)
```

Now attack it the way Exercise 17.6 attacks the naive queue. Enqueue 0 to 1022, which rotates at |R| = 1, 2, 4, ..., 512 and leaves |F| = 1023, |R| = 0. Dequeue down to the version p whose next dequeue must force the 512-element reversal, and replay that dequeue from p a thousand times:

```python
q = EMPTY_Q
for i in range(1023):
    q = enqueue(q, i)              # rotations at |R| = 1, 2, 4, ..., 512
assert steps == 0                  # nothing has been reversed yet: all lazy
p = q
for i in range(511):
    x, p = dequeue(p)              # p: the 512-element reversal is next in line
assert steps == 511                # the smaller reversals, 1 + 2 + ... + 256
for _ in range(1000):
    x, _ = dequeue(p)              # replay the expensive dequeue 1000 times
    assert x == 511
assert steps == 1023               # the big reversal ran once, not 1000 times
```

Every element was reversed exactly once in total. Change `force` to rerun the thunk on every call instead of caching it, and the replay loop alone does 512,000 reversal steps, 512 per call: the failure of the naive queue again. Memoization alone is not enough either: Exercise 17.8 keeps it but rotates only when F is empty, and a replay attack comes back. The two ingredients only work together.

### Real-time queues

A worst-case bound needs no accounting at all, and no usage pattern can break it: if no operation ever costs more than c, replaying one costs at most c too. Hood and Melville (1981) made the functional queue O(1) worst case by doing the reversal a few steps at a time. Okasaki (1995) found a much simpler construction from the same lazy pieces:

- **Make the rotation incremental.** `rotate(f, r, acc)` computes `f ++ reverse(r) ++ acc` one O(1) cell at a time, moving one element of r onto the accumulator for each cell of f. It needs |r| = |f| + 1 so that the reversal finishes exactly when f does, and that is exactly when the banker's queue rotates.
- **Keep a schedule.** A pointer s to the first unevaluated cell of the front, with |s| = |F| − |R|. Every operation forces exactly one cell of s and advances it. When s runs out, |R| = |F| + 1 and the next rotation starts.

The schedule forces each cell of the front before any dequeue reaches it, so no operation does more than one O(1) step of rotation: **O(1) worst case** per operation, persistent or not.

```python
def rotate(f, r, acc):
    """Lazy f ++ reverse(r) ++ acc, one O(1) step per cell. Needs |r| == |f| + 1."""
    def cell():
        global steps
        steps += 1
        c = f.force()
        y, r_rest = r
        if c is None:                          # r has exactly one element left
            return (y, acc)
        return (c[0], rotate(c[1], r_rest, ready((y, acc))))
    return Susp(cell)

# A real-time queue is (front stream, rear cons list, schedule), |schedule| == |f| - |r|.
RT_EMPTY = (EMPTY, None, EMPTY)

def exec1(f, r, s):
    c = s.force()                              # force exactly one cell of the front
    if c is not None:
        return (f, r, c[1])
    f = rotate(f, r, EMPTY)                    # schedule used up: |r| == |f| + 1
    return (f, None, f)

def rt_enqueue(q, x):
    f, r, s = q
    return exec1(f, (x, r), s)

def rt_dequeue(q):
    f, r, s = q
    x, rest = f.force()
    return x, exec1(rest, r, s)
```

A test that operates on randomly chosen old versions, checks every answer against a plain list, and measures the most rotation work any single call does:

```python
import random

versions = [(RT_EMPTY, [])]                    # (queue, the list it should hold)
worst = 0
for _ in range(20000):
    q, ref = random.choice(versions)           # operate on ANY old version
    before = steps
    if ref and random.random() < 0.45:
        x, q2 = rt_dequeue(q)
        assert x == ref[0]
        versions.append((q2, ref[1:]))
    else:
        versions.append((rt_enqueue(q, len(versions)), ref + [len(versions)]))
    worst = max(worst, steps - before)
assert worst == 1                              # never more than one rotate step per call
```

In practice the banker's queue is usually faster, because it does less bookkeeping per operation; the real-time queue is for code where a latency bound matters more than throughput. Both are why a lazy functional language can offer an O(1) persistent queue without any mutation.

## 17.6 Finger Trees

A deque, an indexable sequence, a priority queue, an ordered set and an interval tree are usually five structures. Hinze and Paterson's **2-3 finger tree** (2006) is one persistent structure that provides all five, by changing one parameter.

**Shape.** A finger tree is empty, a single element, or a `Deep` node holding a **prefix** and a **suffix** of 1 to 4 elements each (the "fingers"), plus a **middle** finger tree whose elements are 2-3 nodes (`Node2` or `Node3`) of the outer element type. The middle's middle holds nodes of nodes, so level k of the spine holds complete 2-3 trees of depth k. The ends of the sequence sit at the top of the structure, which is the point: the elements touched most are the cheapest to reach.

To push x onto the back, add it to the suffix if the suffix has fewer than 4 elements. If the suffix is full, `[a, b, c, d]`, it becomes `[d, x]` and `Node3(a, b, c)` is pushed onto the back of the middle tree, by the same rule one level down. Pushing 1 to 10 in order:

```
after 5:   Deep [1]  Empty                                  [2, 3, 4, 5]
after 6:   Deep [1]  (Single N3(2,3,4))                     [5, 6]
after 9:   Deep [1]  (Deep [N3(2,3,4)] Empty [N3(5,6,7)])   [8, 9]
after 10:  Deep [1]  (Deep [N3(2,3,4)] Empty [N3(5,6,7)])   [8, 9, 10]
```

**Costs.** A push reaches the middle only when a digit is full, and it leaves that digit with two elements, so that level overflows again only after three more pushes; deeper levels are reached geometrically less often, like the carries of a counter. Pushes and pops at either end are **amortized O(1)**. Hinze and Paterson keep the middle tree lazy and use the debit argument of Section 17.5, so these bounds hold under persistent use. **Concatenation** is O(log(min(n₁, n₂))) and **splitting** at position i is O(log(min(i, n − i))); both work down the spine, regrouping the loose digit elements into 2-3 nodes at each level.

**Measures.** Each node caches a **measure** of its subtree, taken from a **monoid**: an associative operation ⊕ with an identity element. The measure of a node is the ⊕ of its children's measures, left to right, so it is maintained in O(1) whenever a node is built. A `split` with a predicate that is false and then true as elements are added left to right walks down the tree, skipping every digit and subtree whose cached measure does not flip the predicate.

With the size measure (each element measures 1, ⊕ is +), finding index 6 (0-based, the element 7) in the tree above goes: the outer prefix [1] measures 1, which is ≤ 6, so skip it and look for index 5 in the middle; the middle's prefix N3(2,3,4) measures 3, which is ≤ 5, so skip it and look for index 2; the middle's middle is empty; the middle's suffix starts with N3(5,6,7), and index 2 inside it is 7. Three cached measures were consulted and no element was scanned one by one.

Changing the monoid changes the structure:

| Element measure, ⊕, identity | Split predicate | Result |
|---|---|---|
| 1, +, 0 | running size > i | Indexable sequence: index, split and concatenate in O(log n). This is Haskell's `Data.Sequence`. |
| priority, max, −∞ | running max ≥ max of the whole tree | Max-priority queue: the root's measure is the maximum, and split finds and removes it in O(log n). |
| key, "rightmost key", no key | running key ≥ k | Ordered sequence (elements kept sorted): insert, delete and search by key in O(log n), and merge. |
| (low, high), componentwise max, (−∞, −∞) | running max high ≥ q | Interval tree (intervals sorted by low endpoint): the first interval reaching q contains q if its low endpoint is ≤ q, and otherwise no interval does. |

The table is the real contribution. The tree code is written once against an abstract monoid, and each structure is a few lines of instance declaration. Here is what `split` computes, written as a linear scan so the semantics are easy to check; the finger tree computes exactly this in O(log n) by skipping subtrees whose measures cannot flip the predicate:

```python
from collections import namedtuple

Monoid = namedtuple("Monoid", "identity op measure")

def split(m, pred, xs):
    """What a finger tree split computes: the first x at which pred becomes true
    on the running measure. The tree does it in O(log n) by skipping subtrees
    whose cached measure cannot flip pred; this reference version scans."""
    acc = m.identity
    for i, x in enumerate(xs):
        acc = m.op(acc, m.measure(x))
        if pred(acc):
            return xs[:i], x, xs[i + 1:]
    return xs, None, []

size     = Monoid(0, lambda a, b: a + b, lambda x: 1)
priority = Monoid(float("-inf"), max, lambda job: job[1])
interval = Monoid((float("-inf"), float("-inf")),    # (largest low, largest high)
                  lambda a, b: (max(a[0], b[0]), max(a[1], b[1])),
                  lambda iv: iv)

assert split(size, lambda n: n > 3, list("finger")) == (list("fin"), "g", list("er"))

jobs = [("a", 3), ("b", 9), ("c", 4), ("d", 9)]
top = max(p for _, p in jobs)          # in the tree: the root's cached measure, O(1)
assert split(priority, lambda p: p >= top, jobs)[1] == ("b", 9)

ivs = [(1, 4), (2, 3), (5, 9), (6, 7)]  # kept sorted by low endpoint
_, hit, _ = split(interval, lambda m: m[1] >= 6, ivs)
assert hit == (5, 9) and hit[0] <= 6    # first interval reaching 6; it contains 6
```

The low-endpoint half of the interval measure is not used by this query. It is the ordered-sequence key, used to split by low endpoint when inserting a new interval in its sorted place.

**In practice.** Haskell's `Data.Sequence` (in the `containers` library) is a finger tree specialised to the size measure, with O(1) length, O(log(min(i, n − i))) indexing and O(log(min(n₁, n₂))) concatenation, and the `fingertree` package exposes the general measured version. The price is constant factors: each `Deep` node, its digits and their cached measures are several allocations per element, so for plain stack or queue use, a list or the banker's queue is faster. The finger tree is for when one sequence needs several of these operations at once.

## 17.7 Functional Data Structures

Functional languages favor immutable structures:
- Thread-safe by default
- Undo/redo trivial
- Predictable performance

**Examples:**
- Clojure's persistent vectors
- Haskell's persistent maps
- Scala's immutable collections

Each of those bullets deserves unpacking, because they are the practical reasons persistence is worth its overhead.

**Thread-safe by default** is the big one. Every concurrency hazard in [Chapter 18](ch18-concurrent-data-structures.md) (torn reads, lost updates, iterator invalidation) comes from one thread mutating what another is reading. If nothing is ever mutated, there is nothing to synchronize. Readers need no locks at all, and a writer publishes a new version with a single atomic pointer swap. This is why Clojure's concurrency story is as simple as it is.

**Undo/redo becomes free.** Keeping a stack of old roots *is* the undo history; no command objects, no inverse operations, no replay. Editors and CAD tools built on persistent structures get unlimited undo as a side effect of the data model.

**Predictable performance** cuts both ways honestly. Persistent structures avoid the latency spikes of a dynamic array's O(n) resize, but they allocate constantly, which puts pressure on the garbage collector. The constant factors are genuinely worse than mutable equivalents, typically 2–4× for a HAMT versus a good mutable hash table.

**Where persistence earns its cost:**

- **Version control.** Git is a persistent data structure, which is exactly why committing a one-line change to the Linux kernel does not copy the kernel (details below).
- **Databases.** MVCC (multi-version concurrency control) in PostgreSQL is partial persistence: readers see a consistent snapshot at their transaction's start while writers proceed, without either blocking the other (details below). CouchDB and Datomic go further and keep every version permanently.
- **Filesystems.** ZFS and Btrfs are copy-on-write; a snapshot is just a retained old root, which is why it is instant and initially free.
- **UI frameworks.** React's rendering model assumes immutable props, so change detection is a reference comparison rather than a deep traversal.
- **Debugging.** Time-travel debuggers replay old versions directly, because they still exist.

**The cost side**, stated plainly: 2–4× slower on write-heavy single-threaded workloads, higher memory use and allocation churn, and worse cache locality than a flat array. The wide-trie designs mitigate that last one but do not eliminate it. Persistence is the right default in concurrent and versioned settings, and the wrong one in a tight numerical loop.

### Persistence in the wild: Git and MVCC

**Git's object store** is built from four object types, each named by the hash of its content (SHA-1, or SHA-256 in repositories created with that option). A *blob* is a file's bytes, a *tree* is a directory listing of (mode, name, hash) entries, a *commit* names one root tree and its parent commits, and a *tag* names another object. Edit `src/lib/util.c` and commit, and Git writes a new blob, new trees for `src/lib`, `src` and the root, and a new commit. That is path copying, with the directory path as the path; every other blob and tree is shared, by hash, with the parent commit.

Naming objects by content adds two things path copying alone does not give. Sharing is global rather than only along history: identical files anywhere, in any commit, are one blob, and reverting a file reuses its old blob. And equal hashes mean equal subtrees, which makes the store a **Merkle DAG** (the structure Dynamo uses to compare replicas in [Chapter 31](../volume-5/ch31-real-world-case-studies.md)): `git diff` skips any pair of subtrees whose hashes match without opening them, and `git fetch` transfers only the objects the other side lacks. Merge commits have two parents, so the history is confluent (Exercise 17.1). A branch is a mutable name for an immutable root, the same atomic root pointer as above, and `git gc` is a garbage collector: it deletes objects that no branch, tag or reflog entry can reach. (Packfiles also delta-compress objects on disk; that is storage compression, separate from the structural sharing.)

**MVCC** keeps old versions of rows so that readers can work from a snapshot. PostgreSQL never overwrites a row in an UPDATE: it writes a new row version, and each version records the transaction that created it (`xmin`) and the one that superseded or deleted it (`xmax`). A reader compares those stamps against its snapshot to decide which version it sees. That is the fat node method of Section 17.3 applied per row, version-stamped values with a lookup for the newest one visible at the reader's version, and like fat nodes the history accumulates in place, so PostgreSQL needs `VACUUM` to reclaim versions no snapshot can still see. InnoDB and Oracle instead update rows in place and keep old versions in undo logs, rebuilding an older row by applying undo records backwards. LMDB takes the path-copying route: its B+ tree is copy-on-write, a write transaction copies the root-to-leaf paths it touches and publishes a new root, and a reader keeps using the root it started with. Spanner's timestamped row versions and Delta Lake's versioned table log are covered in [Chapter 31](../volume-5/ch31-real-world-case-studies.md) (Sections 31.1 and 31.4).

## 17.8 Historical Context

Driscoll, Sarnak, Sleator, and Tarjan's 1986 paper "Making Data Structures Persistent" (journal version 1989) is the foundational work. It defined partial and full persistence and introduced fat nodes, node copying and node splitting, proving that any pointer-based structure with bounded in-degree can be made partially or fully persistent with O(1) amortized time and space per update step and no slowdown on access. That is a much stronger and more general result than the path-copying technique most implementations actually use. Sarnak and Tarjan applied it the same year to planar point location with persistent search trees. Confluent persistence was named later, by Driscoll, Sleator and Tarjan in their work on catenable lists (1994), and Brodal (1996) made the update cost of bounded-degree partial persistence O(1) in the worst case.

Chris Okasaki's *Purely Functional Data Structures* (1998), which grew out of his 1996 CMU thesis, addressed the complementary question: which structures can be implemented efficiently *without any mutation at all*? His treatment of amortization under persistence is the subtle part. The usual credit argument breaks when an expensive operation can be re-executed by replaying an old version, and Okasaki's solution using lazy evaluation and memoization (Section 17.5) is why the book remains standard reading. Hood and Melville had made functional queues O(1) worst case in 1981 by spreading the reversal over many operations; Okasaki's 1995 real-time queue reached the same bound much more simply with lazy evaluation and a schedule.

Finger search trees, which keep a "finger" at a position of interest so that nearby searches are fast, go back to Guibas, McCreight, Plass and Roberts (1977). Ralf Hinze and Ross Paterson's 2-3 finger trees (2006) brought the idea into purely functional programming, with a monoid annotation that made one structure serve as sequence, priority queue and search tree; Haskell's `Data.Sequence` is built on it.

Phil Bagwell introduced the Hash Array Mapped Trie in 2001. Rich Hickey built Clojure's collections on it and on the 32-way bit-partitioned vector in 2007, which more than anything else moved persistent structures from a functional-programming specialty into general practice. Bagwell and Tiark Rompf's RRB trees (2011) added efficient concatenation to those vectors. Git, written by Linus Torvalds in 2005, put a content-addressed persistent structure in front of most working programmers.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**17.1 ★ Which level of persistence?** Classify each system as partial, full, or confluent persistence, and name the shape of its version history (line, tree, or DAG).

1. PostgreSQL MVCC, as described in 17.7: a transaction reads the snapshot that existed when it started, and writers only ever modify the current state.
2. An editor with an undo *tree* (Vim and Emacs both have one): you can undo back to any earlier state, make a new edit there, and the abandoned branch stays reachable.
3. Git, including merge commits.
4. A ZFS filesystem with read-only snapshots.

<details>
<summary>Solution</summary>

| System | Level | Version history | Why |
|--------|-------|-----------------|-----|
| PostgreSQL MVCC | Partial | Line | Old snapshots are readable, but every write goes to the newest state. |
| Undo tree | Full | Tree | Editing an old state creates a new branch from it, so updates apply to any version. |
| Git | Confluent | DAG | A merge commit has two parents: two versions combine into one. |
| ZFS read-only snapshots | Partial | Line | Snapshots are retained old roots that can be read but not written; only the live filesystem changes. |

The ZFS answer changes if you use *clones*, which are writable copies of a snapshot. Writing to a clone updates an old version, which makes the history a tree: full persistence.

</details>

**17.2 ★ Trace a second path copy.** Start from the two versions in 17.2: v1 holds 50, 30, 70, 10, and `v2 = insert(v1, 35)`. Now run `v3 = insert(v2, 60)`. Which nodes does this call allocate? Which nodes does v3 share with v2, and which with v1? How many `Node` objects exist across all three versions, and how many would three full copies need?

<details>
<summary>Hint</summary>

Follow the search path for 60 from the root of v2. Only the nodes on that path are copied.

</details>

<details>
<summary>Solution</summary>

The search path for 60 in v2 is A'(50), then right to C(70), then left to an empty slot. So the call copies A' and C and allocates one new leaf:

```
v3 root = A''(50)
         /        \
     B'(30)      C'(70)        A'', C' are copies; F(60) is new
     /    \       /
  D(10)  E(35)  F(60)
```

- **Allocated by this call:** A''(50), C'(70), F(60). That is 3 nodes: 2 copies plus the new leaf.
- **Shared with v2:** B'(30), D(10), E(35). v3's left subtree is exactly v2's left subtree, the same objects.
- **Shared with v1:** only D(10). Every other v1 node (A, B, C) has since been replaced on some copied path.

Totals: v1 has 4 nodes, v2 added 3 (A', B', E), v3 added 3 (A'', C', F), so 10 `Node` objects back all three versions. Three independent copies would need 4 + 5 + 6 = 15.

</details>

**17.3 ★★ Find the bug.** A colleague wants persistence without writing a recursive copy, so they copy the root and then reuse an existing in-place insert:

```python
def _insert_mutating(node, key):
    """Ordinary ephemeral BST insert: modifies the tree in place."""
    if key < node.key:
        if node.left is None:
            node.left = Node(key, None, None)
        else:
            _insert_mutating(node.left, key)
    elif key > node.key:
        if node.right is None:
            node.right = Node(key, None, None)
        else:
            _insert_mutating(node.right, key)

def insert(root, key):
    if root is None:
        return Node(key, None, None)
    new_root = Node(root.key, root.left, root.right)   # copy the root...
    _insert_mutating(new_root, key)                    # ...then insert into the copy
    return new_root
```

Build v1 holding 50, 30, 70 with the chapter's correct `insert`, then call `v2 = insert(v1, 20)` with this one. What does an in-order traversal of v1 print afterwards? Why did the colleague's tests, which inserted into a one-node tree and checked both versions, pass?

<details>
<summary>Hint</summary>

The new root is a copy, but its child pointers are not. What object does `new_root.left` point at?

</details>

<details>
<summary>Solution</summary>

v1 prints `[20, 30, 50, 70]`: the "old" version has the new key in it.

`new_root.left` is the *same* node 30 that v1's root points at. `_insert_mutating` walks from `new_root` to that shared 30 and sets its `left` field in place, so the change is visible through both roots. Persistence is broken for every insert that lands two or more levels below the root.

The one-node test passed by accident. Inserting 40 into a tree holding only 50 attaches the new leaf directly to `new_root`, which really is a fresh copy, so v1 is untouched. The bug only appears when the modified node is below the root.

The fix is the rule from 17.2: **every node whose pointers change must be copied**, and that is every node on the root-to-insertion path, not just the root. The chapter's recursive `insert` does exactly that by building a new node at each level of the recursion. A good regression test records the in-order keys of every old version and asserts they never change after later operations.

</details>

**17.4 ★★ The price of an unbalanced persistent tree.** Insert the keys 1, 2, ..., n in increasing order into the chapter's path-copying BST (no balancing), keeping every version. Exactly how many `Node` objects are allocated in total? Evaluate it for n = 1000 and compare with an ephemeral BST and with a balanced persistent tree.

<details>
<summary>Solution</summary>

When key k is inserted, the current tree is a right-leaning chain 1 → 2 → ... → k−1, and the search path for k visits all k−1 nodes. Each of them gets a new right pointer, so all are copied, plus one new leaf: **k allocations** for the k-th insert.

Total: 1 + 2 + ... + n = n(n+1)/2, which is Θ(n²). For n = 1000 that is 500,500 nodes, all of them reachable from some retained version, so none can be freed.

An ephemeral BST fed the same input allocates 1,000 nodes (it is just as slow, Θ(n²) comparisons, but it does not keep the waste). A balanced persistent tree copies O(log n) nodes per insert, so O(n log n) in total: on the order of n log₂ n ≈ 10,000 for n = 1000, plus a few extra copies per rotation. Even random insertion order into the unbalanced tree averages about 750 allocations for n = 100, against 5,050 for sorted input.

This is the point of the line in 17.2 that balance matters more under persistence: an unbalanced ephemeral tree wastes time, but an unbalanced persistent tree also turns that time into permanent memory.

</details>

**17.5 ★★ HAMT bitmap indexing.** A HAMT node stores a 32-bit bitmap (bit i set means logical slot i is occupied, bit 0 is least significant) and a compact array holding only the occupied children, in slot order. One node has bitmap `0b10110010` and children `['a', 'b', 'c', 'd']`.

1. Which logical slots are occupied, and which child is in each?
2. Look up slot 5 and slot 6.
3. Write `physical_index(bitmap, slot)`, `lookup(bitmap, children, slot)`, and `with_child(bitmap, children, slot, child)`. The last one must return a *new* bitmap and children list without modifying the inputs, since the old node may be shared with an older version. What does adding child `'x'` at slot 3 produce?

<details>
<summary>Hint</summary>

The physical position of slot s is the number of occupied slots below s, which is a population count of the bitmap masked to bits 0 through s−1.

</details>

<details>
<summary>Solution</summary>

1. Bits 1, 4, 5, and 7 are set, so slot 1 → `'a'`, slot 4 → `'b'`, slot 5 → `'c'`, slot 7 → `'d'`.
2. Slot 5: bit 5 is set. The bits below it are `0b10010` (bits 1 and 4), popcount 2, so the answer is `children[2] == 'c'`. Slot 6: bit 6 is clear, so the slot is empty and the lookup fails without touching the array.
3. The three functions:

```python
def physical_index(bitmap, slot):
    return bin(bitmap & ((1 << slot) - 1)).count("1")

def lookup(bitmap, children, slot):
    if not (bitmap >> slot) & 1:
        return None
    return children[physical_index(bitmap, slot)]

def with_child(bitmap, children, slot, child):
    """Return a NEW (bitmap, children); the inputs are not modified."""
    i = physical_index(bitmap, slot)
    if (bitmap >> slot) & 1:                                # replace
        return bitmap, children[:i] + [child] + children[i + 1:]
    return bitmap | (1 << slot), children[:i] + [child] + children[i:]

bm, ch = 0b10110010, ['a', 'b', 'c', 'd']
assert lookup(bm, ch, 5) == 'c' and lookup(bm, ch, 6) is None
bm2, ch2 = with_child(bm, ch, 3, 'x')
assert bm2 == 0b10111010 and ch2 == ['a', 'x', 'b', 'c', 'd']
assert ch == ['a', 'b', 'c', 'd']                           # old node intact
assert lookup(bm2, ch2, 5) == 'c'                           # index shifted, lookup still right
```

Adding slot 3: one occupied slot (slot 1) lies below it, so `'x'` goes at physical index 1. The new bitmap is `0b10111010` and the new array is `['a', 'x', 'b', 'c', 'd']`. Note that `'b'`, `'c'`, and `'d'` all moved one position right, yet lookups still find them, because the physical index is recomputed from the bitmap every time. In production code the popcount is a single instruction (`int.bit_count()` in Python 3.10+, `POPCNT` on x86).

</details>

**17.6 ★★★ Amortization breaks under persistence.** Here is the classic two-list queue made persistent with immutable cons cells: `None` is the empty list and `(head, tail)` is a cell.

```python
steps = 0

def reverse(lst):
    global steps
    out = None
    while lst is not None:
        steps += 1
        head, lst = lst
        out = (head, out)
    return out

def enqueue(q, x):
    front, back = q
    return (front, (x, back))          # O(1)

def dequeue(q):
    front, back = q
    if front is None:                  # front ran out: reverse back into front
        front, back = reverse(back), None
    x, front = front
    return x, (front, back)
```

Ephemerally, this queue is O(1) amortized: each element is moved by `reverse` once. Enqueue 0 through n−1 into `(None, None)` to get version `q`. Then (a) dequeue all n elements in a chain, always using the latest version, and (b) call `dequeue(q)` n times on the *same* version `q`. How many `reverse` steps does each pattern take? Explain what went wrong with the amortized argument, and how Okasaki's approach from Section 17.5 repairs it.

<details>
<summary>Hint</summary>

In pattern (b), does the work done by one call's `reverse` help the next call?

</details>

<details>
<summary>Solution</summary>

In `q`, `front` is empty and `back` holds all n elements.

- **(a) Chain:** the first dequeue reverses n cells, producing a version whose `front` holds the rest. The next n−1 dequeues pop from that `front` with no reversal. Total: **n steps**, O(1) amortized, exactly as in the ephemeral analysis.
- **(b) Replay:** every call receives the same `q` with an empty `front`, so every call reverses all n cells again. The reversed list built by one call is returned inside that call's new version, which the caller discards. Total: **n² steps**, O(n) per operation.

Measured with n = 1000: 1,000 steps for (a), 1,000,000 for (b).

The amortized argument charges the expensive reversal to the n cheap enqueues that preceded it, which works only if that "credit" is spent once. Persistence lets you return to version `q` as often as you like, and each return spends the same credit again. Any amortized bound that relies on an expensive operation happening rarely is vulnerable in the same way.

Okasaki's fix is to make the expensive work *shared* rather than repeated. The reversal is created as a lazy suspension stored inside the version itself and memoized when it is first forced, and the queue creates it early (as soon as the back list grows longer than the front) so that enough cheap operations have already paid for it. Every version that descends from `q` holds the *same* suspension object, so whichever one forces it first pays, and the rest reuse the memoized result. The debt is paid once per version, not once per use, and O(1) amortized holds even under persistence. Section 17.5 builds this queue (the banker's queue) and proves the bound.

</details>

**17.7 ★★ Index arithmetic in a 32-way vector.** A `PVector` from Section 17.4 with the default `bits=5` holds n = 1,000,000 elements, built by appending 0, 1, 2, ... in order.

1. Where does the tail start, how many elements does it hold, what is `shift`, and how many children does the root have?
2. Which slot does `v[777_777]` take at each level?
3. How many nodes does `v.set(777_777, x)` copy, and how many slots do the copies hold in total?
4. Of the 1,000,000 appends, how many pushed a tail into the trie, and how many grew a new root level?

<details>
<summary>Solution</summary>

1. The tail offset is ((1,000,000 − 1) >> 5) << 5 = 31,249 × 32 = 999,968, so the tail holds the 32 elements 999,968 to 999,999. The trie holds the other 999,968 elements in 31,249 full leaves. Since 32² = 1,024 < 31,249 ≤ 32³ = 32,768, three levels of internal nodes sit above the leaves: `shift = 15`. Each root child covers 1,024 leaves, so the root has ⌈31,249 / 1,024⌉ = 31 children.
2. 777,777 is below the tail offset, so it is in the trie. In binary it is `10111 10111 10001 10001`: slot 23 of the root, slot 23 of the next node, slot 17 of the next, and slot 17 of the leaf. Check: 23 × 32,768 + 23 × 1,024 + 17 × 32 + 17 = 777,777.
3. One node per level: the root (31 slots), two internal nodes (32 each) and the leaf (32), so 4 nodes and 127 slots. A mutable array writes 1 slot; copying the whole vector would write 1,000,000.
4. An append pushes the tail exactly when the tail is full, which happens when the current count is a positive multiple of 32: counts 32, 64, ..., 999,968, so 31,249 pushes, one per leaf. The root grows when the number of leaves passes 2^shift: from 32 to 33 leaves (shift 5 to 10) and from 1,024 to 1,025 (shift 10 to 15), so twice. The other 968,751 appends copied only the tail.

</details>

**17.8 ★★★ Memoization is not enough.** Keep `Susp`, `append`, `reverse`, `enqueue` and `dequeue` from Section 17.5, but change `check` to rotate only when the front is empty, the way the naive queue does. Used single-threaded, this is still O(1) amortized. Find a persistent usage pattern that makes it cost Θ(n) per operation, measure it for n = 1000, and explain why the banker's `check`, which rotates as soon as |R| > |F|, is immune to the same pattern.

<details>
<summary>Hint</summary>

Memoization only saves work when two futures force the *same* suspension. Which call creates the rotation suspension, and how soon after can it be forced?

</details>

<details>
<summary>Solution</summary>

Enqueue 0 to n − 1. The first enqueue sees an empty front and rotates [0] into it; the rest go to the rear, leaving |F| = 1, |R| = n − 1. Now, from that same version q, dequeue twice, over and over. The first dequeue empties the front, so its `check` builds a rotation suspension inside the version it returns. That is a *new* object on every call, shared with no other future, so memoization never gets a chance. The second dequeue forces it at once: n − 1 reversal steps per round.

```python
def check(lf, f, lr, r):                 # replaces the check of Section 17.5
    if lf > 0:
        return (lf, f, lr, r)
    return (lr, append(f, reverse(r)), 0, None)    # rotate only when F is empty

n = 1000
q = EMPTY_Q
for i in range(n):
    q = enqueue(q, i)
assert (q[0], q[2]) == (1, n - 1)        # 0 was rotated into the front at once
steps = 0
for _ in range(n):
    _, q1 = dequeue(q)                   # empties the front: builds a NEW rotation
    dequeue(q1)                          # ...and forces it immediately
assert steps == 999_001                  # 999 per round, plus 1 for the first rotation
```

The banker's `check` defeats this because of where it puts the work. A rotation created by any operation sits behind all |F| elements of the front, so a future must perform |F| more dequeues before it can force that rotation, and those dequeues pay its debits. A pattern that keeps going back to q and creating fresh rotations never gets far enough to force them. Running the same loop with the banker's `check` (where q has |F| = 511 and |R| = 489) does 3 reversal steps in total. Laziness makes repeated work shareable; early scheduling guarantees that unshared work has been paid for before it runs.

</details>

**17.9 ★★ Pick the measure.** A music player keeps a playlist as a finger tree of `(title, seconds)` songs, and needs both (a) "which song is playing t seconds into the playlist, and how far into it?" and (b) "what is the i-th song?" in O(log n), from one tree. Give the monoid and the two split predicates, and check them with the reference `split` from Section 17.6 on `[("Intro", 95), ("Blue", 240), ("Static", 185), ("Coda", 60)]`.

<details>
<summary>Hint</summary>

A pair of monoids, combined componentwise, is again a monoid.

</details>

<details>
<summary>Solution</summary>

Measure each song as the pair (1, seconds), combine pairs by adding componentwise, with identity (0, 0). Associativity and the identity law hold in each component, so they hold for the pair. Every song adds at least 1 to the count and a non-negative duration, so the running totals never decrease and each predicate below flips from false to true exactly once, which is what `split` needs.

- (a) Split where the running seconds exceed t. The song found is playing, and it started at the total seconds of the left part, which the tree has as the measure of that part.
- (b) Split where the running count exceeds i.

```python
songs = [("Intro", 95), ("Blue", 240), ("Static", 185), ("Coda", 60)]   # (title, seconds)
both = Monoid((0, 0), lambda a, b: (a[0] + b[0], a[1] + b[1]),
              lambda song: (1, song[1]))                    # (count, total seconds)

def playing_at(t):                     # (a): the song playing t seconds in
    left, song, _ = split(both, lambda m: m[1] > t, songs)
    played = sum(s for _, s in left)   # in the tree: the measure of `left`
    return song[0], t - played         # title, and how far into it we are

assert playing_at(0) == ("Intro", 0)
assert playing_at(95) == ("Blue", 0)
assert playing_at(400) == ("Static", 65)
assert split(both, lambda m: m[0] > 2, songs)[1][0] == "Static"   # (b): song index 2
```

At t = 400 the running seconds are 95, 335, 520: the first to exceed 400 is "Static", which started at 335, so it is 65 seconds in. The same tree also supports moving a song (split it out, concatenate it elsewhere) in O(log n) while keeping both answers correct, because every node's cached pair is rebuilt as the tree is reassembled.

</details>

---

## Where this connects

- [Chapter 18: Concurrent Data Structures](ch18-concurrent-data-structures.md). The concurrency hazards immutability removes outright
- [Chapter 7: Binary Search Trees](../volume-1/ch07-binary-search-trees.md). The BST being made persistent here
- [Chapter 5: Stacks and Queues](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md). The two-stack queue whose amortized bound Section 17.5 rebuilds to survive persistence
- [Chapter 31: Real-World Case Studies](../volume-5/ch31-real-world-case-studies.md). MVCC in Spanner and the versioned table log of Delta Lake
