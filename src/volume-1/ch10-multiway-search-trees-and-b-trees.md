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

### Minimum degree and the height bound

The algorithms below are easiest to state with the **minimum degree** t ≥ 2, the notation of CLRS: every node except the root holds between t − 1 and 2t − 1 keys (so an internal one has between t and 2t children), and a non-empty root holds between 1 and 2t − 1. This is a B-tree of even order m = 2t. The code calls the two limits `MAX_KEYS = 2t − 1` and `MIN_KEYS = t − 1`. The even order is what makes single-pass updates work: a full node of 2t − 1 keys splits around its median into two legal nodes of t − 1 keys (Section 10.3), and two minimal nodes plus the separator between them merge into a node of exactly 2t − 1 keys (Section 10.4). Exercise 10.6 asks what goes wrong with an odd order.

The lower limit is what bounds the height. Count edges, so a tree of height h has h + 1 levels and a search reads at most h + 1 nodes. The thinnest tree of height h has a root with one key and two children, then at least 2t nodes at depth 2, and in general at least 2t^(d−1) nodes at depth d ≥ 1, each with at least t − 1 keys. So

n ≥ 1 + (t − 1) × Σ_{d=1}^{h} 2t^(d−1) = 1 + 2(t^h − 1) = 2t^h − 1,

and therefore **h ≤ log_t((n + 1)/2)** in the worst case.

Put in numbers: with 8-byte keys and 8-byte child pointers, t = 500 (up to 999 keys and 1,000 children per node) fills a 16 KB page, InnoDB's default page size. For n = 10⁹ keys, log₅₀₀(5 × 10⁸) ≈ 3.22, so h ≤ 3: no root-to-leaf path has more than 4 nodes. The tree cannot be shorter either: with every node full, 3 levels hold at most 1000³ − 1 = 999,999,999 keys, one short of a billion. Every such tree has exactly 4 levels, whatever order the keys arrived in. Since a node is one page and one page is one disk read, a cold lookup costs 4 reads. The root is always cached, which makes it 3, and the second level (at most 1,000 pages, about 16 MB) usually fits in the buffer pool as well, leaving 2. A balanced binary tree over the same keys has about log₂ 10⁹ ≈ 30 levels. Exercise 10.3 repeats the calculation for m = 200.

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

## 10.4 Deletion

Insertion can only overflow a node. Deletion has two new problems: removing a key can **underflow** a node (leave it with fewer than t − 1 keys), and the key may sit in an internal node, where taking it out would leave two children with no separator between them.

Bayer and McCreight's original algorithm deletes first and repairs underflow on the way back up, which may cascade to the root. The version here, from CLRS, mirrors the proactive splitting of Section 10.3. Insertion never descends into a full node; deletion never descends into a **minimal** one. The invariant is:

> Whenever the deletion moves into a node other than the root, that node has at least t keys, one more than the minimum.

With that guarantee, the node can lose a key (to a leaf deletion below, or to a merge of two of its children) and still be legal, so nothing ever has to be fixed on the way back up. The deletion is a single pass from root to leaf, with no parent pointers and no stack of ancestors.

At a node x, find the first position i with `key <= x.keys[i]`, exactly as search does. Then one of three cases applies.

**Case 1: the key is in x and x is a leaf.** Remove it. By the invariant x had at least t keys (or is the root), so it still has at least t − 1.

**Case 2: the key is `x.keys[i]` and x is internal.** Let y = `x.children[i]` be the child just left of the key and z = `x.children[i + 1]` the child just right of it.

- **2a.** If y has at least t keys, find the key's **predecessor** k′, the largest key in y's subtree (follow the rightmost child down to a leaf). Overwrite the key with k′, then recursively delete k′ from y. The invariant holds for y because it has t keys.
- **2b.** Otherwise, if z has at least t keys, do the same with the **successor**, the smallest key in z's subtree.
- **2c.** Otherwise y and z both have t − 1 keys. **Merge** them: move the key down from x into y, append all of z's keys and children to y, and remove the key and the pointer to z from x. y now holds (t − 1) + 1 + (t − 1) = 2t − 1 keys, including the key to delete, so recursively delete the key from y.

**Case 3: the key is not in x and x is internal.** If the key is in the tree at all, it is in the subtree c = `x.children[i]`. If c has at least t keys, just descend. If it has only t − 1, top it up first:

- **3a. Borrow** (a rotation through the parent). If an adjacent sibling has at least t keys, move the separator between them down from x into c, and move the sibling's nearest key up into x to replace it. If the nodes are internal, the sibling's nearest child pointer moves across with it, so c gains one key and one child. This is the multiway version of a BST rotation: in-order sequence and key counts in x are unchanged.
- **3b. Merge.** If both adjacent siblings (or the only one) have t − 1 keys, merge c with a sibling and the separator between them, as in 2c. The merged node has 2t − 1 keys and x loses one.

Then descend into c (or the merged node). If x is a leaf and the key is not in it, the key is not in the tree, and the deletion stops.

**Shrinking the root.** The root is the one node allowed to have fewer than t keys, so a merge in case 2c or 3b can take its only key. The root is then an empty node with a single child, and that child becomes the new root. This is the mirror image of a root split: the tree loses a level on every path at once, which is the only way its height decreases, so the leaves stay at the same depth.

### Worked example

Take t = 2, so every non-root node holds 1 to 3 keys. Inserting 10, 20, 30, 40, 50, 60 into an empty tree with the code from Section 10.3 gives

```
        [20 40]
       /   |    \
   [10]  [30]  [50 60]
```

Now delete 30, 10, 50 and 40, in that order.

- **Delete 30 (case 3a, borrow).** At the root, 30 is not present and belongs in child 1, `[30]`, which has t − 1 = 1 key. Its left sibling `[10]` is also minimal, but its right sibling `[50 60]` has 2 keys. Rotate: the separator 40 comes down into the child, giving `[30 40]`, and 50 goes up to replace it. Then case 1 removes 30 from the leaf.

  ```
          [20 50]
         /   |    \
     [10]  [40]  [60]
  ```

- **Delete 10 (case 3b, merge).** 10 belongs in child 0, `[10]`, which is minimal. It has no left sibling, and its right sibling `[40]` is minimal too. Merge `[10]`, the separator 20 and `[40]` into `[10 20 40]`; the root drops to `[50]`. Case 1 removes 10.

  ```
          [50]
         /    \
    [20 40]  [60]
  ```

- **Delete 50 (case 2a).** 50 is in the root, which is internal. The left child `[20 40]` has 2 keys, so 50 is overwritten by its predecessor 40, and 40 is deleted from the left child by case 1. Result: `[40]` with children `[20]` and `[60]`.

- **Delete 40 (case 2c, then the root shrinks).** 40 is in the root and both children are minimal. Merge `[20]`, 40, `[60]` into `[20 40 60]`. The root has no keys left, so `[20 40 60]` becomes the root and the height drops from 1 to 0. Case 1 removes 40, leaving the single leaf `[20 60]`.

<figure>
{{#include ../images/btree-borrow-merge.svg}}
<figcaption>The first two deletions. A borrow moves one key through the parent and leaves the parent's key count alone; a merge pulls the separator down, so the parent loses a key.</figcaption>
</figure>

Borrowing is tried first because it is local: three nodes change, no node is freed, and the parent keeps its key count. Merging frees a node but costs the parent a key, which is why the parent must have had t keys to begin with.

### Cost

Each level does a constant number of node operations: at most one borrow or merge, which touches the node, one sibling and the parent, and shifts O(t) keys. Cases 2a and 2b add a walk down to find the predecessor or successor, along the same path the recursive delete then follows. So deletion reads and writes O(h) = O(log_t n) nodes and does O(t log_t n) CPU work, **worst case**, not amortized. The cost is the same order as bottom-up deletion, but the single pass has a practical advantage shared with proactive splitting: once the deletion has moved below a node, nothing further down can change that node, so a concurrent implementation can release its lock immediately instead of holding locks on the whole path.

The price is some unnecessary work. The fix-ups happen on the way down whether or not they turn out to be needed, so deleting a key that is not in the tree may still borrow or merge. The tree stays valid either way.

### What real databases do instead

Production B+ trees mostly do not enforce the minimum occupancy on deletion.

- **PostgreSQL** never merges partly full index pages. A page is removed only once it is completely empty, and that happens later, during VACUUM.
- **InnoDB** (MySQL) merges a page with a neighbour only when its fill drops below `MERGE_THRESHOLD`, 50% by default.
- Many engines do not even remove the record at once. InnoDB marks deleted records and a background purge removes them later; SQL Server leaves "ghost records" for a cleanup task. The delete itself only flips a flag.

The reasons are practical. Deletes are often followed by inserts into the same key ranges, so merging a page at half full and splitting it again shortly after is wasted I/O and log volume. A merge or borrow modifies three pages (two siblings and the parent), each of which must be locked and logged for crash recovery, and that is the part of a B-tree that is hardest to make concurrent. Johnson and Shasha showed that unless deletes outnumber inserts, freeing pages only when they are empty costs little space utilization compared with merging at half full. The cost is that the height bound from Section 10.2 no longer holds in terms of the current number of keys: a tree that grew to a billion keys and then lost most of them keeps its height. Rebuilding the index (`REINDEX`, `OPTIMIZE TABLE`) compacts it, typically by bulk loading (Section 10.6).

## 10.5 A Complete Implementation

Here is the whole B-tree in one listing: search, insertion with proactive splitting, and single-pass deletion. Search and insertion are the code from Section 10.3, with `split_child` and `split_root` filled in. `T` is the minimum degree t; keys are assumed distinct, as in a unique index.

```python
T = 2                       # minimum degree
MAX_KEYS = 2 * T - 1
MIN_KEYS = T - 1

class BNode:
    def __init__(self, is_leaf):
        self.keys = []
        self.children = []
        self.is_leaf = is_leaf

def btree_search(node, key):
    i = 0
    while i < len(node.keys) and key > node.keys[i]:
        i += 1
    if i < len(node.keys) and key == node.keys[i]:
        return (node, i)
    if node.is_leaf:
        return None
    return btree_search(node.children[i], key)

# ---- insertion: never descend into a full node ----

def split_child(parent, i):
    """Split the full child parent.children[i] around its median."""
    full = parent.children[i]
    mid = len(full.keys) // 2               # T - 1, since the node holds 2T - 1 keys
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

def btree_insert(root, key):
    if len(root.keys) == MAX_KEYS:
        root = split_root(root)             # the only way the tree grows taller
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

# ---- deletion: never descend into a minimal node ----

def btree_delete(root, key):
    _delete(root, key)
    if not root.keys and not root.is_leaf:
        root = root.children[0]             # the only way the tree grows shorter
    return root

def _delete(node, key):
    """Delete key from node's subtree. node is the root or has at least T keys."""
    i = 0
    while i < len(node.keys) and key > node.keys[i]:
        i += 1
    found = i < len(node.keys) and node.keys[i] == key
    if found and node.is_leaf:                          # case 1
        node.keys.pop(i)
    elif found:                                         # case 2
        left, right = node.children[i], node.children[i + 1]
        if len(left.keys) > MIN_KEYS:                   # 2a: predecessor
            node.keys[i] = max_key(left)
            _delete(left, node.keys[i])
        elif len(right.keys) > MIN_KEYS:                # 2b: successor
            node.keys[i] = min_key(right)
            _delete(right, node.keys[i])
        else:                                           # 2c: merge
            merge(node, i)
            _delete(left, key)
    elif not node.is_leaf:                              # case 3
        if len(node.children[i].keys) == MIN_KEYS:
            i = fill_child(node, i)
        _delete(node.children[i], key)
    # otherwise: a leaf without the key, so the key is not in the tree

def max_key(node):
    while not node.is_leaf:
        node = node.children[-1]
    return node.keys[-1]

def min_key(node):
    while not node.is_leaf:
        node = node.children[0]
    return node.keys[0]

def fill_child(parent, i):
    """Give the minimal child parent.children[i] an extra key (case 3).
    Returns the index of the child that now covers the same key range."""
    if i > 0 and len(parent.children[i - 1].keys) > MIN_KEYS:
        borrow_from_left(parent, i)
    elif i < len(parent.keys) and len(parent.children[i + 1].keys) > MIN_KEYS:
        borrow_from_right(parent, i)
    elif i < len(parent.keys):
        merge(parent, i)
    else:
        merge(parent, i - 1)                # the last child merges into its left sibling
        i -= 1
    return i

def borrow_from_left(parent, i):
    child, left = parent.children[i], parent.children[i - 1]
    child.keys.insert(0, parent.keys[i - 1])            # separator comes down
    parent.keys[i - 1] = left.keys.pop()                # sibling's last key goes up
    if not left.is_leaf:
        child.children.insert(0, left.children.pop())

def borrow_from_right(parent, i):
    child, right = parent.children[i], parent.children[i + 1]
    child.keys.append(parent.keys[i])
    parent.keys[i] = right.keys.pop(0)
    if not right.is_leaf:
        child.children.append(right.children.pop(0))

def merge(parent, i):
    """Merge children i and i + 1 of parent around the separator keys[i]."""
    left = parent.children[i]
    right = parent.children.pop(i + 1)
    left.keys.append(parent.keys.pop(i))
    left.keys.extend(right.keys)
    left.children.extend(right.children)
```

The predecessor in case 2a is found by a separate walk (`max_key`) before the recursive delete follows the same path. A disk-based version would fetch those pages once and keep them in the buffer pool, so the walk costs no extra reads.

### Testing it

Deletion has many cases and most bugs only show up several operations later, so test it against something too simple to get wrong: a sorted Python list. The test applies random inserts and deletes to both, and after every operation checks the B-tree invariants:

- every non-root node has between `MIN_KEYS` and `MAX_KEYS` keys, and an internal root has at least one key,
- every internal node has exactly one more child than keys,
- all leaves are at the same depth,
- an in-order traversal equals the reference list. This checks sorted order within nodes and between separators in one go, since any misplaced key would show up out of order.

```python
import random
from bisect import bisect_left

def check(root):
    """Assert the B-tree invariants and return the keys in order."""
    keys, leaf_depths = [], set()

    def walk(node, depth):
        assert len(node.keys) <= MAX_KEYS
        assert node is root or len(node.keys) >= MIN_KEYS
        if node.is_leaf:
            assert not node.children
            leaf_depths.add(depth)
            keys.extend(node.keys)
        else:
            assert len(node.children) == len(node.keys) + 1
            for j, child in enumerate(node.children):
                walk(child, depth + 1)
                if j < len(node.keys):
                    keys.append(node.keys[j])

    assert root.is_leaf or root.keys
    walk(root, 0)
    assert len(leaf_depths) <= 1
    return keys

def random_test(t, ops, key_range, seed):
    global T, MAX_KEYS, MIN_KEYS
    T, MAX_KEYS, MIN_KEYS = t, 2 * t - 1, t - 1
    rng = random.Random(seed)
    root, ref = BNode(is_leaf=True), []
    for step in range(ops):
        p_insert = 0.7 if step < ops // 2 else 0.3      # grow, then shrink
        key = rng.randrange(key_range)
        j = bisect_left(ref, key)
        present = j < len(ref) and ref[j] == key
        if rng.random() < p_insert:
            if not present:
                root = btree_insert(root, key)
                ref.insert(j, key)
        else:
            root = btree_delete(root, key)              # absent keys too
            if present:
                ref.pop(j)
        assert check(root) == ref
        assert (btree_search(root, key) is not None) == (key in ref)

for t in (2, 3, 4):
    for seed in range(1000):
        random_test(t, ops=200, key_range=100, seed=seed)
print("3000 random sequences passed")
```

The insert probability starts at 0.7 and drops to 0.3 halfway, so each sequence grows a tree several levels deep and then shrinks it, often back to an empty leaf, which exercises root shrinking. A small key range makes repeated and absent keys common. The 3,000 sequences (600,000 operations) run in a few seconds and reach every branch of `_delete` and `fill_child`; t = 2 matters most, because with only 1 to 3 keys per node, borrows and merges happen constantly.

## 10.6 B+ Trees

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

### Range scans with leaf links

A range query such as `WHERE key BETWEEN lo AND hi` descends once, to the leaf where `lo` would be, and then walks right along the leaf links until it passes `hi`. Internal nodes are never revisited. Using the separator convention in the figure above (a key equal to a separator lives in the subtree to its right):

```python
from bisect import bisect_left, bisect_right

class BPlusNode:
    def __init__(self, is_leaf):
        self.keys = []
        self.children = []   # internal nodes only
        self.values = []     # leaves only: values[j] belongs to keys[j]
        self.next = None     # leaves only: the leaf to the right
        self.is_leaf = is_leaf

def find_leaf(root, key):
    node = root
    while not node.is_leaf:
        node = node.children[bisect_right(node.keys, key)]
    return node

def range_scan(root, lo, hi):
    """Yield (key, value) for every lo <= key <= hi, in key order."""
    leaf = find_leaf(root, lo)
    j = bisect_left(leaf.keys, lo)
    while leaf is not None:
        while j < len(leaf.keys):
            if leaf.keys[j] > hi:
                return
            yield leaf.keys[j], leaf.values[j]
            j += 1
        leaf, j = leaf.next, 0
```

(`bisect_right(keys, key)` counts the separators ≤ key, which is the index of the child to follow. It is the binary-search version of the linear loop in `btree_search`.)

For example, in this B+ tree with up to 4 entries per leaf (built by `bulk_load` below from the keys 10, 20, …, 130):

```
                    [50 90 110]
      /          /        \           \
[10 20 30 40] → [50 60 70 80] → [90 100] → [110 120 130]
```

`range_scan(root, 35, 85)` reads the root, follows child 0 because 35 < 50, starts at 40 in the first leaf, takes all of the second leaf, and stops at 90 in the third: 4 node reads for 5 results.

**Cost.** If a leaf holds up to L entries and the query returns k of them, the scan reads h + 1 nodes to reach the first leaf and then about one more leaf per L results (up to twice that if leaves are only half full), so O(log_t n + k/L) node reads in the worst case. A plain B-tree can answer the same query by an in-order traversal, with a similar count of nodes, but the results are spread across all levels: the traversal keeps a stack of h nodes and keeps going back up into internal nodes between leaves. The B+ leaf chain needs only the current leaf in memory, lets a database cursor resume from where it stopped without descending again, and, when the leaves were written in key order (as bulk loading does), reads consecutive pages that the disk and the operating system can prefetch. Doubly linked leaves give the same for descending scans (`ORDER BY key DESC`).

### Bulk loading

Building an index on an existing table by inserting n keys one at a time does O(n log_t n) node visits, rewrites each leaf many times, and in random key order touches pages in random order. It also leaves the tree loosely packed. With proactive splitting, ascending keys are the worst case: the rightmost leaf fills to 2t − 1 keys, splits into two halves of t − 1, and every later key goes to the right half, so the left half is never touched again. Inserting 100,000 ascending keys into the Section 10.5 tree with t = 50 produces 2,000 leaves holding 49.0 keys each on average, out of a possible 99. In random order the average is about 68, close to the ln 2 ≈ 69% that analysis of random insertion predicts.

**Bulk loading** builds the tree bottom-up instead:

1. Sort the keys (with an external merge sort if they do not fit in memory).
2. Fill leaves left to right, each as full as desired, and link each to the next.
3. Build the level above from the list of leaves: each parent takes up to a full node's worth of consecutive children, and its separators are the smallest keys of its second, third, … children. Repeat on the list of parents until a level has a single node, the root.

```python
def pack(items, cap):
    """Cut items into runs of cap. If the last run is under half full,
    share the last two runs evenly, so every run is at least half full."""
    runs = [items[i:i + cap] for i in range(0, len(items), cap)]
    if len(runs) >= 2 and len(runs[-1]) < cap // 2:
        both = runs[-2] + runs[-1]
        runs[-2:] = [both[:len(both) // 2], both[len(both) // 2:]]
    return runs

def bulk_load(pairs, cap):
    """Build a B+ tree from (key, value) pairs already sorted by key.
    Leaves hold up to cap entries; internal nodes have up to cap children."""
    level = []
    for run in pack(pairs, cap):                    # the leaf level
        leaf = BPlusNode(is_leaf=True)
        leaf.keys = [k for k, _ in run]
        leaf.values = [v for _, v in run]
        if level:
            level[-1].next = leaf
        level.append(leaf)
    if not level:
        return BPlusNode(is_leaf=True)
    lows = [leaf.keys[0] for leaf in level]         # smallest key under each node
    while len(level) > 1:                           # one level up at a time
        parents, parent_lows = [], []
        for run in pack(list(zip(level, lows)), cap):
            node = BPlusNode(is_leaf=False)
            node.children = [child for child, _ in run]
            node.keys = [low for _, low in run[1:]]
            parents.append(node)
            parent_lows.append(run[0][1])
        level, lows = parents, parent_lows
    return level[0]

pairs = [(k, "r%d" % k) for k in range(10, 140, 10)]
root = bulk_load(pairs, 4)
assert root.keys == [50, 90, 110]
assert [k for k, _ in range_scan(root, 35, 85)] == [40, 50, 60, 70, 80]
```

Every node except possibly the last one or two on each level is completely full, all leaves are at the same depth because every level is built whole, and `pack` keeps the last nodes at least half full so the result is a legal tree. After the sort, the work is O(n): every page is written exactly once, in order, which on disk means long sequential writes instead of n random read-modify-write cycles. The sort itself is O(n log n) comparisons but only a few sequential passes over the data. On a large table this makes index creation many times faster than repeated insertion, and the index comes out roughly half the size of one built from ascending inserts.

Completely full leaves have a cost: the first insert into any of them splits it. A table that will keep receiving inserts across its key range should be loaded with some free space in each leaf. PostgreSQL's `CREATE INDEX` sorts the rows and builds the B-tree bottom-up exactly like this, leaving leaf pages 90% full by default (the index's `fillfactor`). The same idea fixes the ascending-insert problem above: when PostgreSQL splits the rightmost page on a level, it leaves the left page `fillfactor` full instead of splitting it evenly, so a table keyed by an increasing sequence or timestamp still ends up with nearly full pages.

## 10.7 B* Trees

B* trees modify B-trees to keep nodes at least 2/3 full:
- Split only when two sibling nodes are full
- Redistribute between siblings before splitting
- More space-efficient than B-trees

## 10.8 2-3 Trees and 2-3-4 Trees

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

## 10.9 Real-World Applications

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

## 10.10 Performance Characteristics

| Aspect | Binary Tree | B-Tree (m=100) | B+ Tree |
|--------|-------------|----------------|---------|
| Height (1M keys) | ~20 | ~3 | ~3 |
| Disk accesses | 20 | 3 | 3 |
| Node size | Small | Block size | Block size |
| Range scan | Inefficient | Efficient | Most efficient |
| Fan-out | 2 | ~50-200 | ~50-200 |

## 10.11 Variations and Extensions

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

## 10.12 Historical Context

B-trees were introduced by Rudolf Bayer and Edward McCreight in 1970 at Boeing. The "B" stands for "balanced," "broad," or "Boeing" (depending on source).

The B+ tree variant was introduced shortly after, optimized for databases.

Donald Comer provided the comprehensive analysis in his 1979 paper "The Ubiquitous B-Tree," showing how B-trees dominated database indexing.

The single-pass deletion of Section 10.4 is the formulation in Cormen, Leiserson and Rivest's *Introduction to Algorithms* (1990), and later editions with Stein. Theodore Johnson and Dennis Shasha's 1993 paper "B-Trees with Inserts and Deletes: Why Free-at-Empty Is Better Than Merge-at-Half" analysed the relaxed deletion that most database engines use instead.

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

So the B+ tree does 4 page reads for every lookup, while the B-tree needs 6 for any key stored in a leaf, which is most of them (the occasional early hit in an internal node rarely helps). Moving records out of internal nodes is what lets each internal page route 256 ways instead of 36, which is the "higher fan-out, shallower" advantage in Section 10.6. The linked leaves add the second advantage: a range scan of 1,000 consecutive records reads 4 pages to find the start, then about 27 more leaves in order.

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

In a B+ tree, internal keys are only routing copies and every key also appears in a leaf, so searching only at the leaves is the correct design. The descent rule must then match how separators were chosen. With the convention in Section 10.6's figure, where the child to the right of separator s holds keys ≥ s, a key equal to a separator must go *right*, so the loop condition becomes `key >= node.keys[i]` for internal nodes.

</details>

**10.6 ★★★ Implement the split.** Section 10.3's `_insert` calls `split_child(node, i)` and `btree_insert` calls `split_root(root)`, but neither is shown there. (Section 10.5 lists them, so try this first.) Write them for nodes with fields `keys`, `children` and `is_leaf`, where `MAX_KEYS = 2t − 1` for some t ≥ 2. Then explain why this top-down scheme needs `MAX_KEYS` to be odd: what goes wrong with order 5 (`MAX_KEYS = 4`) if you insert 1, 2, 3, 4, 0?

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

**10.7 ★★ Delete by hand.** With t = 2, inserting 1 to 15 in ascending order produces the tree below. Using the algorithm of Section 10.4, delete 1 and then 8. Name the case applied at each node, and show the tree after each deletion.

```
                 [4 8]
          /        |         \
       [2]        [6]        [10 12]
      /   \      /   \      /   |    \
    [1]   [3]  [5]   [7]  [9] [11] [13 14 15]
```

<details>
<summary>Hint</summary>

Deleting 1 starts with two fix-ups on the way down, one per level. Deleting 8 needs a predecessor, and the path to it ends at the last child of a node, which has no right sibling.

</details>

<details>
<summary>Solution</summary>

**Delete 1.** At the root `[4 8]`, 1 belongs in child 0, `[2]`, which is minimal. It has no left sibling and its right sibling `[6]` is minimal too, so **merge (3b)**: `[2]`, 4 and `[6]` become `[2 4 6]` with children `[1] [3] [5] [7]`, and the root drops to `[8]`. Descend into `[2 4 6]`: 1 belongs in child 0, `[1]`, again minimal with a minimal right sibling `[3]`, so **merge** again: `[1 2 3]`, and the node becomes `[4 6]`. Finally **case 1** removes 1 from the leaf.

```
                [8]
           /          \
       [4 6]          [10 12]
      /  |  \        /   |    \
 [2 3] [5]  [7]    [9] [11] [13 14 15]
```

A bottom-up algorithm reaches the same tree here, in the opposite order: `[3]` cannot lend a key, so it would merge at the leaf, leaving `[2]` empty, and then merge again one level up.

**Delete 8.** 8 is in the root, which is internal. Its left child `[4 6]` has 2 = t keys, so **case 2a**: the predecessor is the largest key in that subtree, 7. Overwrite 8 with 7 and delete 7 from `[4 6]`. There, 7 belongs in the last child `[7]`, which is minimal. It has no right sibling and its left sibling `[5]` is minimal, so **merge with the left sibling**: `[5]`, 6, `[7]` become `[5 6 7]` and the node becomes `[4]`. **Case 1** removes 7.

```
                [7]
           /          \
        [4]           [10 12]
       /   \         /   |    \
   [2 3]  [5 6]    [9] [11] [13 14 15]
```

Both trees pass the invariant checks in Section 10.5: every non-root node has 1 to 3 keys and all leaves are at depth 2.

</details>

**10.8 ★★ Sorted input.** Section 10.6 says that inserting keys in ascending order with the proactive-splitting code of Section 10.5 leaves the leaves about half full. (a) Explain exactly why every leaf except the last ends up with t − 1 keys. (b) The table is now bulk loaded instead, with completely full leaves, and afterwards receives inserts of random keys. What happens to the first insert into each leaf, and what does the leaf fill settle to? (c) Why is a fill factor of 100% the right choice for a table that is only ever appended to in key order, such as a log keyed by timestamp?

<details>
<summary>Solution</summary>

(a) A new key larger than every existing key always goes to the rightmost leaf. When that leaf holds 2t − 1 keys, the next insertion splits it on the way down: t − 1 keys stay in the left half, the median moves up, and t − 1 go to the new right leaf, which receives the new key. No later key is smaller than anything in the left half, so it never gains another key. Every leaf except the rightmost is such a left half, with t − 1 of a possible 2t − 1 keys. The internal nodes fill the same way. With t = 50 that is 49 of 99 keys, which is what the measurement in Section 10.6 shows.

(b) Every leaf is full, so the first insert into each one splits it into two halves of t − 1 keys plus the new key: across the tree, utilization falls toward 50% as the inserts spread out, and then climbs back as the halves fill, settling around the ln 2 ≈ 69% of random insertion. The burst of splits right after loading is the reason for leaving free space, such as PostgreSQL's default 90% leaf fill: a leaf can then absorb several inserts before its first split.

(c) If every new key is larger than all existing ones, no insert ever lands in an existing leaf except the rightmost. Free space left in the other leaves would never be used, so it is pure waste: more pages to store, cache and scan. Full leaves are optimal, and splitting the rightmost leaf unevenly (keeping the left page full and starting a nearly empty right page) keeps them full as the table grows.

</details>

---

## Where this connects

- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). The external-memory model that explains why B-trees exist
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). The Bloom filters that make LSM-tree reads viable
