# Chapter 17: Persistent Data Structures

## 17.1 Persistence Defined

A persistent data structure preserves previous versions when modified.

**Types:**
- **Partial persistence**: Query old versions, update current
- **Full persistence**: Query and update any version
- **Confluent persistence**: Merge versions

Every structure so far has been **ephemeral**: modifying it destroys what was there before. Insert into a BST and the old tree is gone. Persistence removes that destruction — an update returns a *new* version while every old version remains valid and queryable.

The naive implementation is to copy the whole structure on every update, which is correct, obvious, and O(n) per operation in both time and space. The entire subject is about achieving persistence without paying that price. The key insight is that an update usually touches a small part of the structure, so the new version can **share** everything it did not touch with the old one.

The three levels of persistence form a strict hierarchy:

| Level | Query | Update | Version structure |
|-------|-------|--------|-------------------|
| Partial | Any version | Newest only | A line |
| Full | Any version | Any version | A tree |
| Confluent | Any version | Any version, plus merge | A DAG |

Confluent persistence is genuinely harder than the other two. When versions can merge, a node can be reachable by exponentially many paths, and the naive analysis of sharing breaks down.

**Immutability is the enabling property.** Sharing is only safe if shared nodes are never modified in place — otherwise a change made through the new version would be visible through the old one, which is exactly what persistence is supposed to prevent. This is why persistent structures and functional programming arrived together.

## 17.2 Persistent BSTs

<figure>
{{#include ../images/path-copying.svg}}
<figcaption>Path copying: only the root-to-insertion path is duplicated.</figcaption>
</figure>

Share unchanged nodes on modification. Inserting 25 requires copying every node on the path from the root down to the insertion point — and only those nodes. Everything hanging off that path is shared with the previous version:

```
Before (version 1):        After (version 2), inserting 25:

      A(50)                  A(50)          A'(50)      ← new root
     /     \                /     \        /      \
  B(30)   C(70)          B(30)   C(70)  B'(30)     │
   /                      /               /   \     │
D(10)                  D(10)          D(10)  E(25)  │
                          ↑              ↑     ↑     │
                          └──────────────┘     │     │
                              shared        new    shared
                                            node   (C(70))

Version 1 root = A, version 2 root = A'.
Copied: A → A', B → B'.  New: E(25).  Shared: D(10), C(70).
```

Note that **B must be copied, not shared** — its right-child pointer changes to point at the new node E. This is the part that is easy to get wrong. Any node whose pointers change must be copied; a node is only shareable if nothing about it changes. Since only nodes along the root-to-leaf path have changed children, exactly O(log n) nodes are copied in a balanced tree.

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
v2 = insert(v1, 25)     # v1 still queryable, unchanged
v3 = insert(v2, 60)     # three coexisting versions
```

There is no mutation anywhere in that function — it only ever constructs new nodes — which is what makes the old roots remain valid.

**This is path copying**, and its cost is the height of the tree:

| Operation | Time | Extra space per version |
|-----------|------|------------------------|
| Insert / delete (balanced) | O(log n) | O(log n) |
| Query any version | O(log n) | — |
| Insert (unbalanced worst case) | O(n) | O(n) |

Balance matters more here than in the ephemeral case, because an unbalanced tree costs you both time *and* permanent space on every update. Red-black trees and AVL trees both path-copy cleanly; the rotations simply produce a few more copied nodes.

**Fat nodes** are the alternative technique: instead of copying a node, store a list of (version, value) pairs inside it and binary search for the right one at query time. This gives O(1) space per update rather than O(log n), at the cost of an O(log m) slowdown on every access for m versions. **Node copying** (Driscoll, Sarnak, Sleator, and Tarjan, 1986) combines both — give each node a small fixed number of extra modification slots, and only copy when they fill — achieving O(1) amortized space with no query slowdown. That paper is where the general theory of making any pointer structure persistent comes from.

## 17.3 Persistent Arrays and HAMTs

Trees path-copy naturally because they are already logarithmic-depth pointer structures. Arrays do not — a persistent array cannot copy 1,000,000 elements per write.

The standard solution is to stop using a flat array and use a **wide, shallow tree** instead, then path-copy that. Clojure's persistent vector is a 32-way branching trie: with a branching factor of 32, a vector of a billion elements is only 6 levels deep, so an update copies 6 nodes of 32 pointers each rather than a billion elements. Depth is ⌈log₃₂ n⌉, which for any realistic n is at most 7 — close enough to constant that these are often described as "effectively O(1)" operations.

```
32-way trie holding 1,000,000 elements — 4 levels deep:

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

**Thread-safe by default** is the big one. Every concurrency hazard in [Chapter 18](ch18-concurrent-data-structures.md) — torn reads, lost updates, iterator invalidation — comes from one thread mutating what another is reading. If nothing is ever mutated, there is nothing to synchronize. Readers need no locks at all, and a writer publishes a new version with a single atomic pointer swap. This is why Clojure's concurrency story is as simple as it is.

**Undo/redo becomes free.** Keeping a stack of old roots *is* the undo history; no command objects, no inverse operations, no replay. Editors and CAD tools built on persistent structures get unlimited undo as a side effect of the data model.

**Predictable performance** cuts both ways honestly. Persistent structures avoid the latency spikes of a dynamic array's O(n) resize, but they allocate constantly, which puts pressure on the garbage collector. The constant factors are genuinely worse than mutable equivalents — typically 2–4× for a HAMT versus a good mutable hash table.

**Where persistence earns its cost:**

- **Version control.** Git is a persistent data structure. Every commit is a new root over a Merkle tree of directory nodes, sharing every unchanged subtree — which is exactly why committing a one-line change to the Linux kernel does not copy the kernel.
- **Databases.** MVCC (multi-version concurrency control) in PostgreSQL is partial persistence: readers see a consistent snapshot at their transaction's start while writers proceed, without either blocking the other. CouchDB and Datomic go further and keep every version permanently.
- **Filesystems.** ZFS and Btrfs are copy-on-write; a snapshot is just a retained old root, which is why it is instant and initially free.
- **UI frameworks.** React's rendering model assumes immutable props, so change detection is a reference comparison rather than a deep traversal.
- **Debugging.** Time-travel debuggers replay old versions directly, because they still exist.

**The cost side**, stated plainly: 2–4× slower on write-heavy single-threaded workloads, higher memory use and allocation churn, and worse cache locality than a flat array — the wide-trie designs mitigate that last one but do not eliminate it. Persistence is the right default in concurrent and versioned settings, and the wrong one in a tight numerical loop.

## 17.5 Historical Context

Driscoll, Sarnak, Sleator, and Tarjan's 1986 paper "Making Data Structures Persistent" is the foundational work: it established the partial/full/confluent taxonomy and proved that any pointer-based structure with bounded in-degree can be made partially persistent with O(1) amortized space overhead per update — a much stronger and more general result than the path-copying technique most implementations actually use.

Chris Okasaki's *Purely Functional Data Structures* (1998), which grew out of his 1996 CMU thesis, addressed the complementary question: which structures can be implemented efficiently *without any mutation at all*? His treatment of amortization under persistence is the subtle part — the usual banker's argument breaks when an expensive operation can be re-executed by replaying an old version, and Okasaki's solution using lazy evaluation and memoization is why the book remains standard reading.

Phil Bagwell introduced the Hash Array Mapped Trie in 2001. Rich Hickey built Clojure's collections on it in 2007, which more than anything else moved persistent structures from a functional-programming specialty into general practice.
