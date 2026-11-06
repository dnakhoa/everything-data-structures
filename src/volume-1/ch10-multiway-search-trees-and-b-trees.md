# Chapter 10: Multiway Search Trees and B-Trees

## 10.1 Beyond Binary: The Need for Multiway Trees

Binary trees require O(log n) levels, which means O(log n) disk accesses for large trees stored on disk. If each level requires a disk read, this is still costly.

B-trees solve this by allowing more than two children per node:

```
Binary tree for 1 million keys:
Height ≈ 20 (with good balance)
Disk accesses for search: 20

B-tree with 1000 children per node:
Height ≈ 3
Disk accesses for search: 3
```

This dramatic reduction in height makes B-trees ideal for disk-based storage.

## 10.2 B-Tree Definition

A B-tree of order m satisfies:

1. Every node has at most m children
2. Every internal node (except root) has at least ⌈m/2⌉ children
3. The root has at least 2 children (unless it's a leaf)
4. A node with k children contains k-1 keys
5. All leaves appear at the same depth

```
B-tree of order 5 (max 4 keys, 5 children):
        ┌───────────────┐
        │ 20 │ 40 │ 60 │
        └───────────────┘
       /    │    │    \
   [0-20) [20-40) [40-60) [60+)
```

## 10.3 B-Tree Operations

<figure>
{{#include ../images/btree-split.svg}}
<figcaption>A node split. The median rises to the parent, keeping every leaf at equal depth.</figcaption>
</figure>

### Search

Similar to BST but with linear search within nodes:

```python
def btree_search(node, key):
    i = 0
    while i < len(node.keys) and key > node.keys[i]:
        i += 1

    if i < len(node.keys) and key == node.keys[i]:
        return (node, i)  # Found

    if node.is_leaf:
        return None  # Not found

    return btree_search(node.children[i], key)
```

### Insert

1. Find leaf where key belongs
2. Insert key (split if node is full)

```python
def btree_insert(root, key):
    if len(root.keys) == MAX_KEYS:
        # Split root
        new_root = split_root(root)
        root = new_root

    _insert(root, key)
    return root

def _insert(node, key):
    i = 0
    while i < len(node.keys) and key > node.keys[i]:
        i += 1

    if node.is_leaf:
        node.keys.insert(i, key)
    else:
        if len(node.children[i].keys) == MAX_KEYS:
            split_child(node, i)
            if key > node.keys[i]:
                i += 1
        _insert(node.children[i], key)
```

### Splitting Nodes

When a node is full, split it:

```
Overflowing node with 5 keys (order 5 allows at most 4):
    ┌─────────────────┐
    │10│20│30│40│50│  ← Split into:
    └─────────────────┘
           ↓
    ┌───────┐   ┌───────┐
    │10│20│  │  │40│50│  (two nodes)
    └───┴───┘   └───┴───┘
           │
       ┌───┴───┐
       │  30   │  ← Median key goes up
       └───────┘
```

## 10.4 B+ Trees

B+ trees are optimized for range queries, common in databases.

### Differences from B-trees

1. Only leaves store data/values; internal nodes store only keys
2. Leaves are linked (usually doubly-linked)
3. Internal nodes are routing nodes (like telephone switching)

```
B+ Tree (internal nodes):
        ┌───────────────────┐
        │   20  │  40  │ 60 │
        └───────────────────┘
        /     │     │     \
    [0-20) [20-40) [40-60) [60+)

Leaves (linked for range queries):
┌──┬──┐   ┌──┬──┬──┐   ┌──┬──┐   ┌──┬──┐
│10│15│ → │25│30│35│ → │40│50│ → │60│70│ → NULL
└──┴──┘   └──┴──┴──┘   └──┴──┘   └──┴──┘
```

Advantages:
- More keys fit in internal nodes (higher fan-out, shallower)
- Leaves linked for efficient range scans
- All data at same depth (predictable I/O)

## 10.5 B* Trees

B* trees modify B-trees to keep nodes at least 2/3 full:
- Split only when two sibling nodes are full
- Redistribute between siblings before splitting
- More space-efficient than B-trees

## 10.6 2-3 Trees and 2-3-4 Trees

2-3 trees are B-trees of order 3:
- 2-node: 1 key, 2 children
- 3-node: 2 keys, 3 children

```
2-node:          3-node:
    ┌───┐         ┌───────┐
    │ 5 │        │ 5 │ 8 │
    └─┬─┘         └───┬─┘
      │               /│\
```

These are conceptual foundations for understanding B-trees and for implementing in-memory balanced trees.

## 10.7 Real-World Applications

**Database Systems**:
- MySQL (InnoDB): B+ trees
- PostgreSQL: B+ trees (primary), other indexes
- Oracle: B+ trees, B* trees
- SQL Server: B+ trees

**File Systems**:
- NTFS (Windows): B+ trees
- HFS+ (macOS): B-trees
- ext4 (Linux): HTrees (generalized B+ trees)
- ReiserFS: B-trees

**Key-Value Stores**:
- LevelDB: Skip list + SSTable with B-tree-like index
- RocksDB: LSM trees (log-structured merge)
- Cassandra: LSM trees (memtable + SSTables), partitioned across nodes

## 10.8 Performance Characteristics

| Aspect | Binary Tree | B-Tree (m=100) | B+ Tree |
|--------|-------------|----------------|---------|
| Height (1M keys) | ~20 | ~3 | ~3 |
| Disk accesses | 20 | 3 | 3 |
| Node size | Small | Block size | Block size |
| Range scan | Inefficient | Efficient | Most efficient |
| Fan-out | 2 | ~50-200 | ~50-200 |

## 10.9 Variations and Extensions

**B+-tree variants**:
- B*-tree: Higher utilization
- B+-tree with bulk loading
- Prefix B-trees: Compress keys

**LSM Trees** (Log-Structured Merge):
- Write-optimized alternative
- Used in Cassandra, RocksDB, LevelDB
- Components: memtable (in-memory), SSTables (disk)

**R-tree**:
- Balanced like a B-tree, but nodes hold bounding rectangles instead of key ranges
- For multi-dimensional range queries
- Used in geographic databases

## 10.10 Historical Context

B-trees were introduced by Rudolf Bayer and Edward McCreight in 1970 at Boeing. The "B" stands for "balanced," "broad," or "Boeing" (depending on source).

The B+ tree variant was introduced shortly after, optimized for databases.

Donald Comer provided the comprehensive analysis in his 1979 paper "The Ubiquitous B-Tree," showing how B-trees dominated database indexing.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**10.1 ★ Legal or not?** In a B-tree of order 5 (Section 10.2), which of these are allowed? Name the rule that each illegal one breaks.

(a) A root with 1 key and 2 children.
(b) A non-root internal node with 1 key and 2 children.
(c) An internal node with 4 keys and 5 children.
(d) A node with 3 keys and 3 children.
(e) A tree with some leaves at depth 2 and others at depth 3.

<details>
<summary>Solution</summary>

(a) **Legal.** Rule 3 only requires the root to have at least 2 children.

(b) **Illegal, rule 2.** A non-root internal node needs at least ⌈5/2⌉ = 3 children (so at least 2 keys). This minimum is what keeps the height logarithmic.

(c) **Legal.** That is the maximum: 5 children (rule 1) and 5 − 1 = 4 keys (rule 4).

(d) **Illegal, rule 4.** A node with k children has exactly k − 1 keys; 3 keys need 4 children.

(e) **Illegal, rule 5.** All leaves must be at the same depth. B-trees grow and shrink only at the root (a root split adds a level everywhere at once), which is how this rule is maintained.

</details>

**10.2 ★★ Insert by hand.** Using `btree_insert` and `_insert` from Section 10.3 with `MAX_KEYS = 3` (a B-tree of order 4, also called a 2-3-4 tree), insert 10, 20, 30, 40, 50, 60, 70 into an empty tree. A full node splits into its middle key, which moves up, and two nodes of one key each. Show the tree after every insertion that causes a split, and the final tree.

<details>
<summary>Hint</summary>

This code splits *proactively*: it splits a full node on the way down, before inserting, even if the new key would not have overflowed it yet.

</details>

<details>
<summary>Solution</summary>

- **10, 20, 30**: all go into the root leaf: `[10 20 30]`, which is now full.
- **40**: the root is full, so `btree_insert` splits it first. 20 moves up into a new root; then 40 goes into the right leaf.

  ```
         [20]
        /    \
    [10]    [30 40]
  ```

- **50**: goes into the right leaf: `[30 40 50]`, now full. No split yet, because splits happen on the way down and this leaf was not full when the descent reached it.
- **60**: the root `[20]` is not full. Descending to child 1, `[30 40 50]` is full, so `split_child` moves 40 up into the root. Since 60 > 40, descend to the new right child and insert.

  ```
         [20 40]
        /   |    \
    [10]  [30]  [50 60]
  ```

- **70**: goes into `[50 60]`, giving `[50 60 70]`. No split.

Final tree:

```
       [20 40]
      /   |    \
  [10]  [30]  [50 60 70]
```

All leaves are at depth 1. The next insert larger than 40 will split `[50 60 70]` on its way down, before touching the leaf.

</details>

**10.3 ★★ How tall can a B-tree get?** Let t = ⌈m/2⌉ be the minimum number of children of a non-root internal node in a B-tree of order m, and assume (as is standard) that every non-root node holds at least t − 1 keys. (a) Show that a B-tree of height h (edges) holds at least 2t^h − 1 keys, so h ≤ log_t((n + 1)/2). (b) For m = 200 and n = 10⁹ keys, what is the maximum height, and how many node reads does a search need in the worst case? Compare with a balanced binary tree.

<details>
<summary>Hint</summary>

Count the minimum number of nodes at each depth: the root may have only 2 children, but every node below it has at least t.

</details>

<details>
<summary>Solution</summary>

(a) Take the thinnest possible tree. Depth 0 is the root with at least 1 key and 2 children. At depth 1 there are at least 2 nodes, at depth 2 at least 2t, and in general at least 2t^(d−1) nodes at depth d ≥ 1, each with at least t − 1 keys. So

n ≥ 1 + (t − 1) × Σ_{d=1}^{h} 2t^(d−1) = 1 + 2(t − 1) × (t^h − 1)/(t − 1) = 2t^h − 1.

Rearranging: t^h ≤ (n + 1)/2, so **h ≤ log_t((n + 1)/2)**.

(b) m = 200 gives t = 100. log₁₀₀(5 × 10⁸) = log₁₀(5 × 10⁸) / 2 ≈ 8.70 / 2 = 4.35, so **h ≤ 4**: at most 5 levels, and a search reads **at most 5 nodes**. In the best case, with every node full (199 keys, 200 children), 3 levels hold only 200³ − 1 ≈ 8 × 10⁶ keys, so at least 4 levels are needed. A billion keys therefore sit in a tree of 4 or 5 levels. A balanced binary tree needs about log₂(10⁹) ≈ 30 levels. In practice the root and the second level (about 200 nodes) stay in memory, so the B-tree costs 2 or 3 disk reads per lookup.

</details>

**10.4 ★★ Why B+ trees fan out further.** Pages are 4096 bytes. Keys are 8 bytes, child pointers are 8 bytes, and each record (the value stored with a key) is 100 bytes. Ignore page headers. (a) What is the maximum fan-out of an internal node in a B-tree that stores records alongside keys in every node, and in a B+ tree whose internal nodes store only keys and pointers? (b) How many records fit in a B+ leaf? (c) With 10⁸ records and every node full, how many levels does each tree have?

<details>
<summary>Hint</summary>

A node with f children holds f − 1 keys. In the B-tree, each key carries its record with it.

</details>

<details>
<summary>Solution</summary>

(a) **B-tree:** f pointers plus f − 1 (key + record) entries: 8f + 108(f − 1) ≤ 4096, so 116f ≤ 4204 and **f = 36**. **B+ tree:** 8f + 8(f − 1) ≤ 4096, so 16f ≤ 4104 and **f = 256**.

(b) Each leaf entry is a key plus a record, 108 bytes: ⌊4096 / 108⌋ = **37 records** per leaf. (Reserving 8 bytes for the next-leaf link still leaves room for 37.)

(c) **B-tree:** a full tree with L levels and fan-out 36 holds 36^L − 1 keys. 36⁵ − 1 ≈ 6.0 × 10⁷ is too few and 36⁶ − 1 ≈ 2.2 × 10⁹ is enough, so **6 levels**.

**B+ tree:** 10⁸ / 37 ≈ 2.7 × 10⁶ leaves. Above them, internal levels with fan-out 256: 256² = 65,536 is too few to index them and 256³ ≈ 1.7 × 10⁷ is enough, so 3 internal levels plus the leaf level: **4 levels**.

So the B+ tree does 4 page reads for every lookup, while the B-tree needs 6 for any key stored in a leaf, which is most of them (the occasional early hit in an internal node rarely helps). Moving records out of internal nodes is what lets each internal page route 256 ways instead of 36, which is the "higher fan-out, shallower" advantage in Section 10.4. The linked leaves add the second advantage: a range scan of 1,000 consecutive records reads 4 pages to find the start, then about 27 more leaves in order.

</details>

**10.5 ★★ Find the bug.** A colleague "simplifies" `btree_search` like this:

```python
def btree_search(node, key):
    i = 0
    while i < len(node.keys) and key > node.keys[i]:
        i += 1
    if node.is_leaf:
        if i < len(node.keys) and node.keys[i] == key:
            return (node, i)
        return None
    return btree_search(node.children[i], key)
```

On the final tree from 10.2, which keys does it fail to find? Explain the bug, and say why the same shape of code *would* be close to correct for a B+ tree.

<details>
<summary>Solution</summary>

It only checks for a match at leaves. In a B-tree every key is stored exactly once, and keys that moved up during splits live **only** in internal nodes. On the tree from 10.2 it fails for **20 and 40**: searching 20, the loop stops at i = 0 because 20 > 20 is false, the root is not a leaf, so it descends into children[0] = `[10]` and returns `None`. 40 likewise descends into `[30]`. The other five keys are found.

The fix is the original order in Section 10.3: check `node.keys[i] == key` at every node, before testing `is_leaf`.

In a B+ tree, internal keys are only routing copies and every key also appears in a leaf, so searching only at the leaves is the correct design. The descent rule must then match how separators were chosen. With the convention in Section 10.4's figure, where the child to the right of separator s holds keys ≥ s, a key equal to a separator must go *right*, so the loop condition becomes `key >= node.keys[i]` for internal nodes.

</details>

**10.6 ★★★ Implement the split.** Section 10.3's `_insert` calls `split_child(node, i)` and `btree_insert` calls `split_root(root)`, but neither is shown. Write them for nodes with fields `keys`, `children` and `is_leaf`, where `MAX_KEYS = 2t − 1` for some t ≥ 2. Then explain why this top-down scheme needs `MAX_KEYS` to be odd: what goes wrong with order 5 (`MAX_KEYS = 4`) if you insert 1, 2, 3, 4, 0?

<details>
<summary>Hint</summary>

A full child has 2t − 1 keys. The middle one, at index t − 1, moves up into the parent at position i, and the right half becomes a new child at position i + 1. Internal nodes also have to split their children list.

</details>

<details>
<summary>Solution</summary>

```python
class BNode:
    def __init__(self, is_leaf):
        self.keys = []
        self.children = []
        self.is_leaf = is_leaf

def split_child(parent, i):
    """Split the full child parent.children[i] around its median."""
    full = parent.children[i]
    mid = len(full.keys) // 2            # t - 1 when the node holds 2t - 1 keys
    right = BNode(full.is_leaf)
    right.keys = full.keys[mid + 1:]
    if not full.is_leaf:
        right.children = full.children[mid + 1:]
        full.children = full.children[:mid + 1]
    median = full.keys[mid]
    full.keys = full.keys[:mid]
    parent.keys.insert(i, median)
    parent.children.insert(i + 1, right)

def split_root(root):
    new_root = BNode(is_leaf=False)
    new_root.children.append(root)
    split_child(new_root, 0)
    return new_root
```

A full node with 2t − 1 keys becomes two nodes of t − 1 keys each, with the median moving up. Both halves meet the minimum of t − 1 keys. The parent is guaranteed to have room for the median, because `_insert` never descends into a full node: it splits first. That invariant is what lets the insertion finish in a single pass down the tree, with no walking back up. Splitting the root is the only way the height grows, and it adds one level to every path at once, which keeps all leaves at the same depth.

Checks worth running: insert a few hundred random keys for t = 2, 3, 4, then assert that every non-root node holds between t − 1 and 2t − 1 keys, that internal nodes have one more child than keys, that keys are sorted within each node and between separators, and that all leaves are at the same depth.

**Why `MAX_KEYS` must be odd.** With order 5, a non-root node needs at least ⌈5/2⌉ − 1 = 2 keys, and a full node has 4. Splitting a 4-key node proactively, *before* inserting, leaves 2 keys on one side and 1 on the other. Insert 1, 2, 3, 4 (the root leaf is now full), then 0: `btree_insert` splits the root into `[1 2]`, median 3, `[4]`, and 0 goes left, giving

```
       [3]
      /   \
 [0 1 2]  [4]
```

The leaf `[4]` has only 1 key, below the order-5 minimum of 2. The top-down scheme only works when a full node splits into two legal halves, which requires 2t − 1 keys. Odd orders such as 5, which give an even `MAX_KEYS`, need the bottom-up approach instead: insert into the leaf first, and split only when it actually overflows to 5 keys, as in the figure in Section 10.3 (2 keys, median, 2 keys).

</details>

---

## Where this connects

- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). The external-memory model that explains why B-trees exist
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). The Bloom filters that make LSM-tree reads viable
