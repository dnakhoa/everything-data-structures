# Chapter 7: Binary Search Trees

## 7.1 The BST Property

A Binary Search Tree maintains elements in sorted order:

```
For every node:
    - All nodes in left subtree have keys < node's key
    - All nodes in right subtree have keys > node's key

Example:
            8
           / \
          3   10
         / \    \
        1   6    14
           / \   /
          4   7 13

Inorder traversal: 1, 3, 4, 6, 7, 8, 10, 13, 14 (sorted!)
```

## 7.2 BST Operations

### Search

```python
def bst_search(node, key):
    if node is None or node.key == key:
        return node
    if key < node.key:
        return bst_search(node.left, key)
    return bst_search(node.right, key)
```

Time: O(h) where h is height. Worst case O(n) for degenerate tree.

### Insertion

```python
def bst_insert(root, key):
    if root is None:
        return TreeNode(key)
    if key < root.key:
        root.left = bst_insert(root.left, key)
    else:
        root.right = bst_insert(root.right, key)
    return root
```

Insert as leaf; find position by following search path.

### Deletion

Three cases:
1. **Leaf node**: Simply remove
2. **One child**: Replace node with its child
3. **Two children**: Replace with inorder successor (minimum in right subtree) or inorder predecessor (maximum in left subtree), then delete that successor/predecessor

```python
def bst_delete(node, key):
    if node is None: return None

    if key < node.key:
        node.left = bst_delete(node.left, key)
    elif key > node.key:
        node.right = bst_delete(node.right, key)
    else:  # Found the node to delete
        if node.left is None: return node.right
        if node.right is None: return node.left

        # Node has two children
        successor = min_value(node.right)
        node.key = successor.key
        node.right = bst_delete(node.right, successor.key)

    return node
```

### Minimum and Maximum

```python
def min_value(node):
    current = node
    while current.left:
        current = current.left
    return current

def max_value(node):
    current = node
    while current.right:
        current = current.right
    return current
```

## 7.3 BST Complexity Analysis

| Operation | Average | Worst Case |
|-----------|---------|------------|
| Search | O(log n) | O(n) |
| Insert | O(log n) | O(n) |
| Delete | O(log n) | O(n) |
| Min/Max | O(log n) | O(n) |
| Successor/Predecessor | O(log n) | O(n) |
| Traversal | O(n) | O(n) |

**Average case** assumes randomly inserted keys, yielding approximately balanced trees with height ~log n.

**Worst case** occurs when keys are inserted in sorted order:
```
Inserting: 1, 2, 3, 4, 5

     1
      \
       2
        \
         3
          \
           4
            \
             5

Height = n, operations = O(n)
```

## 7.4 Self-Balancing BSTs

Self-balancing trees maintain height O(log n) regardless of insertion order.

### Height-Balance Definitions

Different balancing criteria define different tree families:

| Tree Type | Balance Criterion |
|-----------|------------------|
| AVL | \|height(left) - height(right)\| ≤ 1 |
| Red-Black | Black-height balanced, no consecutive reds |
| Splay | No explicit criterion, amortized O(log n) |
| Weight-balanced | Size of subtrees within factor |

## 7.5 Threaded Binary Trees

Threaded trees store threads (pointers) to inorder predecessor/successor instead of null pointers:

```c
struct ThreadedNode {
    element_type data;
    struct ThreadedNode *left;
    struct ThreadedNode *right;
    int left_thread;  // true if left points to inorder predecessor
    int right_thread; // true if right points to inorder successor
};
```

```
Threaded Tree:
         4
        / \
       2   6
      /     \
     1       8

Threads shown as dashed:
     1 ──→ 2 ──→ 4 ──→ 6 ──→ 8
```

Advantage: O(1) space for traversal (no stack)
Disadvantage: More complex insert/delete

## 7.6 BST Variants

### Treaps (BST + Heap)

Combine BST property with random heap priorities:

```
Treap example (priorities in parentheses):
            (50)8
           /     \
      (30)3      (70)10
        /   \        \
    (20)1   (40)6   (80)14
```

The BST property holds on keys; heap property holds on priorities. Random priorities ensure expected O(log n) height.

### Skip Lists as BST Alternative

Skip lists can be viewed as a probabilistic alternative to BSTs, with similar complexity but simpler implementation.

### AA-Trees

Simplified red-black tree that only allows right children to be red:
- Similar to 2-3 tree representation
- Simpler delete (no complex cases)
- O(log n) guaranteed

## 7.7 Applications of BSTs

- **Ordered maps**: Python dict (but actually hash-based), C++ map, Java TreeMap
- **Ordered sets**: Python set, C++ set, Java TreeSet
- **Database indexes**: B+ trees (multi-level BSTs)
- **Priority queues**: Can implement with additional min-pointer
- **Finger trees**: For sequence operations with good complexity

## 7.8 Choosing BST vs Alternatives

**Use BST When:**
- Need ordered iteration
- Range queries needed
- Insert/delete balance with search
- Can tolerate O(n) worst case (or using balanced variant)

**Use Hash Table When:**
- Only point queries needed
- Insert/delete heavy
- Can tolerate hash collisions

---

## Where this connects

- [Chapter 8: Self-Balancing Trees](ch08-self-balancing-trees.md) — what to do when this degrades to a linked list
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md) — making a BST persistent, so old versions survive updates
