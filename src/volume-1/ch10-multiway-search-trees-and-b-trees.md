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

    return _insert(root, key)

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
Full node with 4 keys (max):
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
┌──────┬──────┬──────┐    ┌──────┬──────┐
│10│15│25│30│35│ → │40│50│ → NULL
└──────┴──────┴──────┘    └──────┴──────┘
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
- Cassandra: B+ trees (local), distributed indexes

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

**RD-tree** (Recursive Decomposition):
- For multi-dimensional range queries
- Used in geographic databases

## 10.10 Historical Context

B-trees were introduced by Rudolf Bayer and Edward McCreight in 1970 at Boeing. The "B" stands for "balanced," "broad," or "Boeing" (depending on source).

The B+ tree variant was introduced shortly after, optimized for databases.

Donald Comer provided the comprehensive analysis in his 1979 paper "The Ubiquitous B-Tree," showing how B-trees dominated database indexing.

---

## Where this connects

- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) — the external-memory model that explains why B-trees exist
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md) — the Bloom filters that make LSM-tree reads viable
