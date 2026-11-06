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

**Fat nodes** are the alternative technique: instead of copying a node, store a list of (version, value) pairs inside it and binary search for the right one at query time. This gives O(1) space per update rather than O(log n), at the cost of an O(log m) slowdown on every access for m versions. **Node copying** (Driscoll, Sarnak, Sleator, and Tarjan, 1986) combines both: give each node a small fixed number of extra modification slots, and only copy when they fill. Achieving O(1) amortized space with no query slowdown. That paper is where the general theory of making any pointer structure persistent comes from.

## 17.3 Persistent Arrays and HAMTs

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

The **Hash Array Mapped Trie (HAMT)** applies the same structure to maps. Hash the key, then use 5 bits of the hash per level to index into a 32-wide node. The refinement that makes it space-efficient is a bitmap in each node marking which of the 32 slots are occupied, so a node with 3 children stores 3 pointers and a 32-bit mask rather than 32 mostly-null pointers. Population count on the bitmap converts a logical index to a physical one in one instruction.

HAMTs are the backbone of persistent maps in Clojure, Scala, and Haskell, and the same idea appears in Erlang and in immutable-collections libraries for JavaScript.

## 17.4 Functional Data Structures

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

- **Version control.** Git is a persistent data structure. Every commit is a new root over a Merkle tree of directory nodes, sharing every unchanged subtree, which is exactly why committing a one-line change to the Linux kernel does not copy the kernel.
- **Databases.** MVCC (multi-version concurrency control) in PostgreSQL is partial persistence: readers see a consistent snapshot at their transaction's start while writers proceed, without either blocking the other. CouchDB and Datomic go further and keep every version permanently.
- **Filesystems.** ZFS and Btrfs are copy-on-write; a snapshot is just a retained old root, which is why it is instant and initially free.
- **UI frameworks.** React's rendering model assumes immutable props, so change detection is a reference comparison rather than a deep traversal.
- **Debugging.** Time-travel debuggers replay old versions directly, because they still exist.

**The cost side**, stated plainly: 2–4× slower on write-heavy single-threaded workloads, higher memory use and allocation churn, and worse cache locality than a flat array. The wide-trie designs mitigate that last one but do not eliminate it. Persistence is the right default in concurrent and versioned settings, and the wrong one in a tight numerical loop.

## 17.5 Historical Context

Driscoll, Sarnak, Sleator, and Tarjan's 1986 paper "Making Data Structures Persistent" is the foundational work: it established the partial/full/confluent taxonomy and proved that any pointer-based structure with bounded in-degree can be made partially persistent with O(1) amortized space overhead per update. A much stronger and more general result than the path-copying technique most implementations actually use.

Chris Okasaki's *Purely Functional Data Structures* (1998), which grew out of his 1996 CMU thesis, addressed the complementary question: which structures can be implemented efficiently *without any mutation at all*? His treatment of amortization under persistence is the subtle part. The usual banker's argument breaks when an expensive operation can be re-executed by replaying an old version, and Okasaki's solution using lazy evaluation and memoization is why the book remains standard reading.

Phil Bagwell introduced the Hash Array Mapped Trie in 2001. Rich Hickey built Clojure's collections on it in 2007, which more than anything else moved persistent structures from a functional-programming specialty into general practice.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**17.1 ★ Which level of persistence?** Classify each system as partial, full, or confluent persistence, and name the shape of its version history (line, tree, or DAG).

1. PostgreSQL MVCC, as described in 17.4: a transaction reads the snapshot that existed when it started, and writers only ever modify the current state.
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

Ephemerally, this queue is O(1) amortized: each element is moved by `reverse` once. Enqueue 0 through n−1 into `(None, None)` to get version `q`. Then (a) dequeue all n elements in a chain, always using the latest version, and (b) call `dequeue(q)` n times on the *same* version `q`. How many `reverse` steps does each pattern take? Explain what went wrong with the amortized argument, and how Okasaki's approach from 17.5 repairs it.

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

Okasaki's fix is to make the expensive work *shared* rather than repeated. The reversal is created as a lazy suspension stored inside the version itself and memoized when it is first forced, and the queue creates it early (as soon as the back list grows longer than the front) so that enough cheap operations have already paid for it. Every version that descends from `q` holds the *same* suspension object, so whichever one forces it first pays, and the rest reuse the memoized result. The debt is paid once per version, not once per use, and O(1) amortized holds even under persistence. This is the "lazy evaluation and memoization" from 17.5.

</details>

---

## Where this connects

- [Chapter 18: Concurrent Data Structures](ch18-concurrent-data-structures.md). The concurrency hazards immutability removes outright
- [Chapter 7: Binary Search Trees](../volume-1/ch07-binary-search-trees.md). The BST being made persistent here
