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

**Why case 3 is safe.** The successor is the smallest key in the right subtree, so it is larger than everything in the left subtree and no larger than anything left in the right subtree. Putting its key into the deleted node keeps the BST property at that node. And because the successor is a minimum, it has no left child, so removing it from the right subtree is always case 1 or case 2.

**Worked example: deleting 3 from the tree of Section 7.1.** Node 3 has two children, 1 and 6:

```
bst_delete(8, 3)      3 < 8: recurse into the left subtree
bst_delete(3, 3)      found; children 1 and 6, so case 3
  min_value(6)        6 → 4; 4 has no left child, so the successor is 4
  node.key = 4        the node that held 3 now holds 4
  bst_delete(6, 4)    4 < 6: recurse left
  bst_delete(4, 4)    4 is a leaf (case 1): return None, so 6.left = None

Before:                       After:
            8                             8
           / \                           / \
          3   10                        4   10
         / \    \                      / \    \
        1   6    14                   1   6    14
           / \   /                         \   /
          4   7 13                          7 13
```

Only one node is physically unlinked: the leaf that held 4. The node that held 3 stays in place with a new key. Deleting the root 8 instead shows the other sub-case: its successor is 10, which has a right child, so the second call is case 2 and 14 moves up to become the new root's right child.

Copying the key is fine for this key-only tree, but a real map also has to move the value, and any outside pointer to the successor's node (an iterator, a cursor) would suddenly see a different key. That is why `std::map`, whose `erase` may invalidate only iterators to the erased element, relinks the successor *node* into the deleted node's position instead of copying data.

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

**Average case** assumes randomly inserted keys, yielding trees of height Θ(log n). The constant is larger than for a perfectly balanced tree; see below.

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

### The Height of a Randomly Built BST

"Randomly inserted" has a precise meaning: n distinct keys are inserted into an empty tree, all n! insertion orders equally likely, and there are no deletions. Under that model there are two different questions, with different answers: how deep is a typical node (the average search cost), and how deep is the deepest one (the worst search in that tree)?

**It is quicksort's recursion tree.** The first key inserted becomes the root, and every later key is compared with it and sent left or right. After that, the smaller keys build the left subtree among themselves and the larger keys build the right subtree, each still in uniformly random order. That is exactly quicksort with the first element of each subarray as pivot: the root is the first pivot, the two subtrees are the two recursive calls. Each key is compared with precisely its ancestors, so the number of comparisons quicksort makes equals the sum of the depths of all nodes in the BST built from the same sequence (its *internal path length*). Shuffling the input and building a BST does the same comparisons as quicksort with random pivots.

**Average depth.** Number the keys 1 to n by rank. Key j is an ancestor of key i exactly when j is the first key inserted from the range between i and j (inclusive). Until some key from that range arrives, i and j follow the same path, because every node on it is outside the range and sends both the same way. The first key from the range to arrive splits them: if it is j, j becomes an ancestor of i; if it is i, i becomes an ancestor of j; if it is strictly between, they go to different subtrees. Each of the |i − j| + 1 keys in the range is equally likely to come first, so

```
P(j is an ancestor of i) = 1 / (|i − j| + 1)

E[depth of key i] = Σ_{j ≠ i} 1/(|i − j| + 1) = H_i + H_{n−i+1} − 2       (H_m = 1 + 1/2 + ... + 1/m)

Average over all i:  2(1 + 1/n) H_n − 4  ≈  2 ln n  ≈  1.39 log₂ n
```

Multiply by n and you have quicksort's expected comparison count, 2(n + 1)H_n − 4n ≈ 1.39 n log₂ n. So a successful search in a random BST costs on average only about 39% more comparisons than in a perfectly balanced one.

**Expected height.** The deepest node is much deeper than the average one. Devroye (1986) proved that the expected height is asymptotically α ln n, where α ≈ 4.311 is the solution with α ≥ 2 of α ln(2e/α) = 1. That is about 2.99 log₂ n, three times the height of a perfect tree. Reed (2003) sharpened this to α ln n − β ln ln n + O(1) with β ≈ 1.953, and showed that the variance of the height is O(1): almost every random BST has nearly the same height. The second-order term is large at practical sizes, so measured heights sit well below 4.311 ln n:

| n | perfect tree height ⌊log₂ n⌋ | average depth 2(1 + 1/n)H_n − 4 | 2 ln n | height, simulated | 4.311 ln n |
|---|---|---|---|---|---|
| 1,000 | 9 | 11.0 | 13.8 | 19 to 22 | 29.8 |
| 100,000 | 16 | 20.2 | 23.0 | 38 to 41 | 49.6 |
| 1,000,000 | 19 | 24.8 | 27.6 | 50 | 59.6 |

(The simulated column is three random insertion orders for the first two rows and one for the last.)

**What the model does not cover.** Real keys often arrive sorted or nearly sorted (timestamps, auto-increment IDs), and then the "average case" never happens: you get the chain above. Treaps (Section 7.10) and the balanced trees of Chapter 8 remove the dependence on input order. Deletions also break the model. Always replacing a deleted node by its successor takes keys from the right side only, and long random sequences of insertions and deletions slowly push the tree away from the random shape; alternating between successor and predecessor reduces the drift (see Historical Context).

## 7.4 Successor and Predecessor

The *inorder successor* of a node x is the node with the next larger key; the *predecessor* is the node with the next smaller key. They are what an ordered-map iterator's `++` and `--` do, and what Java's `TreeMap.higherKey` and `lowerKey` return. The two cases for the successor follow from the order in which inorder visits nodes:

1. **x has a right subtree.** Inorder visits x and then its entire right subtree, starting with that subtree's leftmost node. So the successor is `min_value(x.right)`: one step right, then left as far as possible.
2. **x has no right subtree.** Then x is the last node visited in some subtree, and the successor is whatever inorder visits after that subtree. Walk up. While x is a right child, its parent was visited *before* it, so keep climbing. The first time you climb up from a left child into a parent p, x was the maximum of p's left subtree, so p is next. If you climb past the root, x was the maximum of the whole tree and has no successor.

<figure>
{{#include ../images/bst-successor.svg}}
<figcaption>The two successor cases on the example tree: a short walk down when a right subtree exists, otherwise a walk up that stops at the first ancestor reached from its left side.</figcaption>
</figure>

**With parent pointers** both cases are direct. Assume each `TreeNode` has a `parent` field (which `bst_insert` and `bst_delete` must then keep up to date):

```python
def successor_node(x):
    if x.right:                      # case 1: leftmost node of the right subtree
        return min_value(x.right)
    p = x.parent                     # case 2: climb until we arrive from a left child
    while p and x is p.right:
        x, p = p, p.parent
    return p                         # None if x was the maximum

def predecessor_node(x):
    if x.left:
        return max_value(x.left)
    p = x.parent
    while p and x is p.left:
        x, p = p, p.parent
    return p
```

On the example tree: the successor of 3 is 4 (right to 6, left to 4), of 7 is 8 (7 and 6 are right children, 3 is a left child, so stop at its parent 8), of 13 is 14 (13 is a left child, one step up), and 14 has none (14 and 10 are right children, then the walk leaves the root).

Each call is O(h) in the worst case. Iterating over the whole tree is cheaper than that suggests: starting at `min_value(root)` and calling `successor_node` n − 1 times crosses each edge at most twice, once going down and once coming up, so the full walk is O(n) and each step is amortized O(1). This is how ordered-map iterators work in practice: libstdc++'s `_Rb_tree_increment` and the Linux kernel's `rb_next` are this two-case walk on a red-black tree with parent pointers.

**Without parent pointers** there are two options. To answer one query, search from the root and remember the last node where the search turned the "useful" way. For the predecessor of a key, every time you go right you have passed a node smaller than the key, and every later such node is larger, so the last one is the answer:

```python
def predecessor(root, key):
    best = None
    node = root
    while node:
        if node.key < key:
            best = node          # a candidate; a larger one may be to the right
            node = node.right
        else:
            node = node.left     # node.key >= key, so the answer is to the left
    return best.key if best else None
```

`predecessor(root, 5)` visits 8 (go left), 3 (best = 3, go right), 6 (go left), 4 (best = 4, go right), then `None`, and returns 4. It is O(h) and works whether or not `key` is in the tree. The successor is the mirror image (Exercise 7.5). To iterate over the tree instead, keep the path from the root on an explicit stack: that is the iterative inorder traversal of Chapter 6, which also gives amortized O(1) per step, at the cost of O(h) memory instead of a parent pointer in every node.

## 7.5 Floor, Ceiling and Range Queries

Ordered maps answer four "nearest key" queries, all variants of the descent above:

| Query | Returns | Java `TreeMap` | C++ `std::map` |
|-------|---------|----------------|----------------|
| lower(k) | largest key < k | `lowerKey` | (`lower_bound`, then step back) |
| floor(k) | largest key ≤ k | `floorKey` | (`upper_bound`, then step back) |
| ceiling(k) | smallest key ≥ k | `ceilingKey` | `lower_bound` |
| higher(k) | smallest key > k | `higherKey` | `upper_bound` |

`predecessor(root, key)` above is lower(k). Floor differs only in returning the key itself when it is present:

```python
def floor_key(root, key):
    best = None
    node = root
    while node:
        if node.key == key:
            return key
        if node.key < key:
            best = node.key      # candidate; a larger one may be to the right
            node = node.right
        else:
            node = node.left
    return best
```

Ceiling swaps `<` for `>` and left for right. On the example tree, floor(5) = 4, floor(12) = 10, ceiling(12) = 13, ceiling(15) = `None`. Each is O(h) worst case. These are the queries behind "the price tier for an order of 37 units" (floor over tier boundaries) or "the next scheduled event after now" (ceiling over timestamps).

**Range queries.** To report every key in [lo, hi] in sorted order, do an inorder traversal but skip any subtree that the BST property says is entirely out of range:

```python
def range_keys(node, lo, hi, out):
    if node is None:
        return
    if lo < node.key:                  # left subtree may hold keys >= lo
        range_keys(node.left, lo, hi, out)
    if lo <= node.key <= hi:
        out.append(node.key)
    if node.key < hi:                  # right subtree may hold keys <= hi
        range_keys(node.right, lo, hi, out)
```

The output is sorted because the traversal is still inorder. Nothing in range is missed: a left subtree is skipped only when node.key ≤ lo, so all its keys are < lo, and a right subtree only when node.key ≥ hi, so all its keys are > hi.

**Cost: O(h + k)** worst case for a tree of height h, where k is the number of keys reported. Every visited node is either reported or lies on the search path for lo or on the search path for hi, so at most k + 2(h + 1) nodes are visited (Exercise 7.6 proves it). On the example tree, `range_keys(root, 5, 12, out)` reports 6, 7, 8, 10 and visits eight nodes: the four reported ones, 3 and 4 (the search path for 5 is 8, 3, 6, 4) and 14 and 13 (the search path for 12 is 8, 10, 14, 13). It never touches 1. On a balanced tree that is O(log n + k): the cost of finding the two ends of the range plus one unit per answer, however large n is. A hash table has no equivalent and must scan all n keys. If you only need *how many* keys are in range, not the keys themselves, subtree sizes (Section 7.7) answer in O(h).

## 7.6 Validating a BST

A validator is worth having whenever a tree's invariant could be broken: in tests for a new balancing scheme, after a tree is loaded from disk or the network, or as a debug assertion after rotations. The classic wrong answer checks each node only against its children:

```python
def is_bst_local(node):            # WRONG: only checks parent-child pairs
    if node is None:
        return True
    if node.left and node.left.key >= node.key:
        return False
    if node.right and node.right.key <= node.key:
        return False
    return is_bst_local(node.left) and is_bst_local(node.right)
```

Change the 7 in the example tree to 9. Every parent-child pair is still in order (9 > 6), so `is_bst_local` returns `True`, but 9 sits in 8's left subtree, and `bst_search(root, 9)` goes right at 8 and reports it missing. The BST property of Section 7.1 is about *all* nodes in a subtree, and a constraint from far up the tree is invisible to a local check.

**Pass the bounds down.** Every node in a subtree must lie in an open interval (lo, hi) fixed by its ancestors. Going left from a node tightens the upper bound to that node's key; going right tightens the lower bound:

```python
def is_bst(node, lo=None, hi=None):
    if node is None:
        return True
    if (lo is not None and node.key <= lo) or (hi is not None and node.key >= hi):
        return False
    return is_bst(node.left, lo, node.key) and is_bst(node.right, node.key, hi)
```

On the broken tree: `is_bst(8)` calls `is_bst(3, None, 8)`, which calls `is_bst(6, 3, 8)`, which calls `is_bst(9, 6, 8)`, and 9 ≥ 8 fails. Using `None` rather than ±∞ for "no bound" keeps it working for any comparable keys, strings included.

**Or check the inorder sequence.** A binary tree is a BST (with distinct keys) exactly when its inorder sequence is strictly increasing. With the explicit-stack inorder traversal from Chapter 6, the check can stop at the first violation:

```python
def is_bst_inorder(root):
    prev = None
    stack, node = [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if prev is not None and node.key <= prev:
            return False
        prev = node.key
        node = node.right
    return True
```

Both versions take O(n) time in the worst case (a valid tree must be read in full) and O(h) space for the recursion or the stack.

## 7.7 Order Statistics: Augmenting with Subtree Size

Two queries a plain BST answers badly: **select(k)**, the k-th smallest key, and **rank(key)**, how many keys are smaller than a given one. An inorder walk answers both, but in O(n) worst case. Store one extra integer in each node and both drop to O(h).

The augmentation is `size`, the number of nodes in the node's subtree, with the invariant

```
node.size = 1 + size(node.left) + size(node.right)        (size of an empty tree = 0)
```

```python
class TreeNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.size = 1              # nodes in this subtree

def size(node):
    return node.size if node else 0

def update(node):
    node.size = 1 + size(node.left) + size(node.right)
```

**Maintaining it.** Insertion and deletion only change the subtrees of nodes on the search path, so `bst_insert` and `bst_delete` need one new line each: recompute the size of every node on the way back up the recursion.

```python
def bst_insert(root, key):
    if root is None:
        return TreeNode(key)
    if key < root.key:
        root.left = bst_insert(root.left, key)
    else:
        root.right = bst_insert(root.right, key)
    update(root)                                    # new
    return root

def bst_delete(node, key):
    if node is None:
        return None
    if key < node.key:
        node.left = bst_delete(node.left, key)
    elif key > node.key:
        node.right = bst_delete(node.right, key)
    else:
        if node.left is None: return node.right
        if node.right is None: return node.left
        successor = min_value(node.right)
        node.key = successor.key
        node.right = bst_delete(node.right, successor.key)
    update(node)                                    # new
    return node
```

Recomputing from the children on the way up, rather than adding or subtracting 1 on the way down, is deliberate: deleting a key that is not in the tree changes nothing, and in case 3 the sizes along the path to the successor shrink too. Recomputation gets both right without special cases. The extra work is O(1) per node on the path, so both operations stay O(h). In the balanced trees of Chapter 8 a rotation changes the subtrees of exactly two nodes; recompute the lower one first, then the upper one, and the augmentation survives rebalancing.

**Select and rank** each walk one root-to-leaf path, using the left subtree's size to decide where to go. Keys are counted from 0, so select(0) is the minimum:

```python
def select(node, k):
    """The k-th smallest key, counting from 0."""
    while node:
        left = size(node.left)
        if k < left:
            node = node.left           # the answer is among the left subtree's keys
        elif k == left:
            return node.key            # exactly k keys are smaller than this one
        else:
            k -= left + 1              # skip the left subtree and this node
            node = node.right
    raise IndexError(k)

def rank(node, key):
    """How many keys in the tree are smaller than key."""
    r = 0
    while node:
        if key <= node.key:
            node = node.left
        else:
            r += size(node.left) + 1   # this node and its whole left subtree are smaller
            node = node.right
    return r
```

The example tree with sizes:

```
              8(9)
             /    \
          3(5)    10(3)
          /  \        \
       1(1)  6(3)     14(2)
             /  \     /
          4(1) 7(1) 13(1)
```

- `select(root, 3)`: at 8, the left size is 5 and 3 < 5, go left. At 3, the left size is 1 and 3 > 1, so k becomes 3 − 2 = 1, go right. At 6, the left size is 1 = k: return **6**. (Sorted: 1, 3, 4, **6**, ...)
- `rank(root, 13)`: at 8, 13 > 8, add 5 + 1 (r = 6), go right. At 10, add 0 + 1 (r = 7), go right. At 14 and then 13, go left. Return **7**: the keys 1, 3, 4, 6, 7, 8, 10.

Counting keys in a range now costs O(h) regardless of how many there are: for integer keys, the count in [lo, hi] is rank(hi + 1) − rank(lo). On the example, [5, 12] holds rank(13) − rank(5) = 7 − 3 = 4 keys, matching what `range_keys` reported.

On a balanced tree all of this is O(log n) worst case, for one extra integer per node. GNU libstdc++ ships it as a policy-based tree (`tree_order_statistics_node_update`, with `find_by_order` and `order_of_key`), and Redis sorted sets apply the same idea to a skip list, storing a span count on each forward link so `ZRANK` is O(log n). Size is the simplest instance of a general technique: any field that can be computed from a node and its children's fields (a subtree sum, a maximum, the largest interval endpoint in an interval tree) can be maintained through inserts, deletes and rotations at no asymptotic cost.

## 7.8 Self-Balancing BSTs

Self-balancing trees maintain height O(log n) regardless of insertion order.

### Height-Balance Definitions

Different balancing criteria define different tree families:

| Tree Type | Balance Criterion |
|-----------|------------------|
| AVL | \|height(left) - height(right)\| ≤ 1 |
| Red-Black | Black-height balanced, no consecutive reds |
| Splay | No explicit criterion, amortized O(log n) |
| Weight-balanced | Size of subtrees within factor |

## 7.9 Threaded Binary Trees

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

## 7.10 BST Variants

### Treaps (BST + Heap)

Combine BST property with random heap priorities:

```
Treap example (priorities in parentheses):
            (10)8
           /     \
      (30)3      (20)10
        /   \        \
    (50)1   (40)6   (70)14
```

The BST property holds on keys; the heap property holds on priorities (a min-heap here: every priority is smaller than its children's). Random priorities ensure expected O(log n) height.

### Skip Lists as BST Alternative

Skip lists can be viewed as a probabilistic alternative to BSTs, with similar complexity but simpler implementation.

### AA-Trees

Simplified red-black tree that only allows right children to be red:
- Similar to 2-3 tree representation
- Simpler delete (no complex cases)
- O(log n) guaranteed

## 7.11 Applications of BSTs

- **Ordered maps**: Python dict (but actually hash-based), C++ map, Java TreeMap
- **Ordered sets**: C++ set, Java TreeSet (Python set is hash-based too)
- **Database indexes**: B+ trees (multi-level BSTs)
- **Priority queues**: Can implement with additional min-pointer
- **Finger trees**: For sequence operations with good complexity

## 7.12 Choosing BST vs Alternatives

**Use BST When:**
- Need ordered iteration
- Range queries needed
- Insert/delete balance with search
- Can tolerate O(n) worst case (or using balanced variant)

**Use Hash Table When:**
- Only point queries needed
- Insert/delete heavy
- Can tolerate hash collisions

## 7.13 Historical Context

The binary search tree was developed independently by several people around 1960. The earliest published descriptions include P. F. Windley ("Trees, forests and rearranging", *The Computer Journal*, 1960), A. D. Booth and A. J. T. Colin (*Information and Control*, 1960), and T. N. Hibbard ("Some combinatorial properties of certain trees with applications to searching and sorting", *Journal of the ACM*, 1962). Hibbard's paper also gave the successor-based deletion of Section 7.2, still called *Hibbard deletion*, and analysed it: deleting a random key from a random BST leaves a random BST. That does not survive further updates. Knott observed in the 1970s that randomness is lost once another insertion follows, and Eppinger's simulations (*Communications of the ACM*, 1983) showed that long random sequences of insertions and Hibbard deletions first improve and then worsen the average path length, while symmetric deletion (alternating successor and predecessor) behaves better.

The average-depth result of Section 7.3 is the same calculation as the average-case analysis of quicksort, which Hoare published in 1961 and 1962. The height took much longer: Devroye proved the 4.311 ln n asymptotic in 1986, and in 2003 Reed and, independently, Drmota determined the second-order term and showed that the variance of the height is bounded.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**7.1 ★ Build a BST by hand.** Insert 50, 30, 70, 20, 40, 60, 80, 35, 45, 65 into an empty BST using `bst_insert`. Draw the result, give its height, and list the nodes `bst_search` visits when looking for 45 and when looking for 62.

<details>
<summary>Solution</summary>

```
            50
          /    \
        30      70
       /  \    /  \
     20   40  60   80
         /  \   \
        35  45   65
```

Height is **3** (for example 50→30→40→35). Inorder gives 20 30 35 40 45 50 60 65 70 80, sorted as expected.

- Search 45: 50 (go left), 30 (go right), 40 (go right), 45 (found). **4 nodes.**
- Search 62: 50 (right), 70 (left), 60 (right), 65 (left), then `None`. **4 nodes visited, not found.** An unsuccessful search always ends at an empty child slot, and that slot is exactly where `bst_insert` would put 62.

</details>

**7.2 ★★ Trace all three deletion cases.** Starting from the tree in 7.1, run `bst_delete` for 20, then 30, then 50. For each, say which case of Section 7.2 applies and draw the tree after the final deletion.

<details>
<summary>Hint</summary>

After 20 is gone, look again at how many children 30 has. For 50, find the minimum of its right subtree, and note how many children that node has.

</details>

<details>
<summary>Solution</summary>

1. **Delete 20.** It is a leaf (case 1): 30's left pointer becomes `None`.
2. **Delete 30.** It now has only a right child, 40 (case 2). `bst_delete` returns `node.right`, so the subtree rooted at 40 (with 35 and 45) moves up to become 50's left child.
3. **Delete 50.** It has two children (case 3). The successor is `min_value(50.right)`: from 70 go left to 60, which has no left child, so the successor is **60**. The root's key becomes 60, and then 60 is deleted from the right subtree. That node has one child (65), so it is case 2 again: 70's left child becomes 65.

```
            60
          /    \
        40      70
       /  \    /  \
     35   45  65   80
```

Case 3 never recurses into another case 3: the successor is the minimum of a subtree, so it has no left child, and removing it is always case 1 or case 2.

</details>

**7.3 ★★ How many insertion orders give the perfect tree?** Inserting 4, 2, 6, 1, 3, 5, 7 into an empty BST produces the perfect tree of height 2 from Chapter 8. Of the 7! = 5040 orders of the keys 1 to 7, how many produce exactly that tree? As a warm-up, how many of the 6 orders of {1, 2, 3} produce a tree of height 2?

<details>
<summary>Hint</summary>

The first key inserted becomes the root forever. After that, the keys smaller than the root and the keys larger than it build their subtrees independently; only their relative order within each side matters.

</details>

<details>
<summary>Solution</summary>

Warm-up: only orders starting with 2 (that is, 2 1 3 and 2 3 1) give the balanced tree. The other **4 of 6** give a chain of height 2.

For 1 to 7: the root must be 4, so 4 comes first. The remaining 6 positions hold the left keys {1, 2, 3} and right keys {5, 6, 7} interleaved in any way: C(6, 3) = 20 ways to choose which positions are left keys. Within the left keys, the order must produce the balanced 3-node tree, which by the warm-up happens in 2 of 6 orders (2 first). Same on the right (6 first). Total:

f(7) = C(6, 3) × f(3) × f(3) = 20 × 2 × 2 = **80**

So 80 / 5040 ≈ 1.6% of orders give the perfect tree. A random order still gives *expected* O(log n) height (Section 7.3), because most of the other 4960 orders give trees that are only slightly worse, not chains. Only 2^(n−1) orders out of n! give a chain: here 64.

</details>

**7.4 ★★ Validating with duplicates.** Section 7.6's `is_bst` assumes distinct keys, but `bst_insert` sends a key equal to the node's key to the right, so inserting 5, 3, 5 builds a tree that `is_bst` rejects. (a) State the invariant that every tree built by `bst_insert` satisfies when duplicates are allowed, and change `is_bst` to check it. (b) Someone suggests instead relaxing `is_bst_inorder` to accept a non-decreasing sequence. Give a tree it wrongly accepts, and say what can go wrong.

<details>
<summary>Hint</summary>

The rule is asymmetric: equal keys may appear on one side only. Which of the two bounds becomes inclusive?

</details>

<details>
<summary>Solution</summary>

(a) `bst_insert` goes left only on `key < root.key`, so the invariant is: every key in the left subtree is **strictly smaller** than the node's key, and every key in the right subtree is **greater than or equal** to it. In bounds form, each subtree's keys lie in the half-open interval [lo, hi): going left still sets an exclusive upper bound, while going right now sets an inclusive lower bound.

```python
def is_bst_dup(node, lo=None, hi=None):
    if node is None:
        return True
    if (lo is not None and node.key < lo) or (hi is not None and node.key >= hi):
        return False
    return is_bst_dup(node.left, lo, node.key) and is_bst_dup(node.right, node.key, hi)
```

The tree from 5, 3, 5 is 5 with left child 3 and right child 5. The right 5 is checked against [5, None), which it satisfies. `bst_delete` keeps this invariant too: in case 3 the successor is the minimum of the right subtree, so every key left in that subtree is still ≥ it.

(b) The tree "5 with a left child 5" has inorder sequence 5, 5, which is non-decreasing, so the relaxed check accepts it. But `bst_insert` can never build it, and `is_bst_dup` rejects it (the left 5 is not < 5). Plain search for 5 still works, but anything that relies on the convention breaks: for example, counting the copies of 5 by finding the first 5 and then looking only in its right subtree reports 1 instead of 2. An inorder sequence cannot tell which side of a node a duplicate is on, so for an asymmetric invariant the bounds version is the one to use.

</details>

**7.5 ★★ Successor without parent pointers.** Section 7.4 finds the predecessor of a key by descending from the root. Write `successor(root, key)` that returns the smallest key in the tree strictly greater than `key` (or `None`), in O(h) time and O(1) extra space, without parent pointers. `key` need not be in the tree. On the example tree in Section 7.1, what does it return for 7, 6, 5 and 14?

<details>
<summary>Hint</summary>

Walk down as in a search. Every time you go left, the node you just left is a candidate answer, and every later candidate is smaller.

</details>

<details>
<summary>Solution</summary>

```python
def successor(root, key):
    best = None
    node = root
    while node:
        if key < node.key:
            best = node          # a candidate; a smaller one may be to the left
            node = node.left
        else:
            node = node.right    # node.key <= key, so the answer is to the right
    return best.key if best else None
```

Each iteration moves down one level, so it takes O(h) time. `best` always holds the smallest key greater than `key` among the nodes seen so far, and the unexplored subtree is the only place a smaller one could be.

On the tree 8, 3, 10, 1, 6, 14, 4, 7, 13:

- 7: path 8 (best = 8, go left), 3 (right), 6 (right), 7 (right), `None`. Returns **8**. This is the "go up to the first ancestor you are a left descendant of" case.
- 6: path 8 (best 8), 3, 6 (right), 7 (best 7, left), `None`. Returns **7**, the minimum of 6's right subtree.
- 5: path 8 (best 8), 3, 6 (best 6), 4 (right), `None`. Returns **6**, even though 5 is not in the tree.
- 14: path 8, 10, 14, all going right, so `best` is never set. Returns **None**.

</details>

**7.6 ★★★ Range queries in O(h + k).** Section 7.5's `range_keys(node, lo, hi, out)` appends every key in [lo, hi] to `out` in sorted order. Prove that it visits at most k + 2(h + 1) nodes, where k is the number of keys reported and h is the tree's height.

<details>
<summary>Hint</summary>

Show that every visited node whose key is *below* lo lies on the search path for lo.

</details>

<details>
<summary>Solution</summary>

**Bound.** Visited nodes are of three kinds: in range (exactly k of them), below lo, or above hi.

Take a visited node v with v.key < lo, and look at each step on the path from the root to v. If the step went *left* from u, the function only does that when lo < u.key, and the search for lo also goes left at u. If the step went *right* from u, then v is in u's right subtree, so u.key < v.key < lo, and the search for lo also goes right at u. Every step agrees with the search for lo, so v is on the search path for lo. That path has at most h + 1 nodes.

The symmetric argument puts every visited node above hi on the search path for hi, another h + 1 nodes at most. Total: at most **k + 2(h + 1)**, which is O(h + k). In the example of Section 7.5, k = 4 and h = 3, and the call visits 8 nodes against a bound of 12.

</details>

**7.7 ★ BST or hash table?** For each service, pick a hash table or a balanced BST and give the deciding reason. (a) A session store that maps random session tokens to user IDs; the only operations are insert, lookup by exact token, and delete. (b) A log index keyed by timestamp; the common query is "all events between 10:00 and 10:05". (c) A leaderboard that must answer "who has the next-highest score after mine?"

<details>
<summary>Solution</summary>

(a) **Hash table.** Only point queries, and no ordering is ever used. Expected O(1) beats O(log n), and random tokens hash well. A BST here pays for an ordering nobody reads.

(b) **Balanced BST** (or a B+ tree on disk, Chapter 10). A time-range query is the `range_keys` pattern of Section 7.5: O(log n + k). A hash table scatters adjacent timestamps across buckets, so it must scan everything.

(c) **Balanced BST** keyed by score. "Next-highest score" is the successor query of Section 7.4, O(log n). A hash table has no notion of "next" and would need an O(n) scan per query.

The pattern from Section 7.12: if any query involves order (next, previous, min, max, range, sorted iteration), the BST wins; if every query is an exact match, the hash table wins.

</details>

**7.8 ★★ Sizes under deletion, and counting a range.** Start from the size-augmented example tree of Section 7.7. (a) Run `bst_delete(root, 3)` (the deletion traced in Section 7.2). Which nodes have their `size` changed, and to what? (b) `rank(hi + 1) − rank(lo)` counts keys in [lo, hi] only for integers. Write `count_range(root, lo, hi)` that works for any comparable keys (strings, floats) in O(h), and check it on [5, 12] after the deletion.

<details>
<summary>Hint</summary>

For (b), write a second descent that counts keys ≤ a given key. It differs from `rank` in one comparison.

</details>

<details>
<summary>Solution</summary>

(a) The recursion visits 8, then the node that held 3 (now 4), then 6, then the leaf 4, which is unlinked. `update` runs on the way back up at each surviving node on that path: **6 becomes 2** (only 7 is left below it), **the node now holding 4 becomes 4** (1, 4, 6, 7), and **8 becomes 8**. Nothing else changes: 10, 14, 13, 1 and 7 keep their sizes because their subtrees did not change.

(b)

```python
def count_leq(node, key):
    """How many keys in the tree are <= key."""
    r = 0
    while node:
        if key < node.key:
            node = node.left
        else:
            r += size(node.left) + 1
            node = node.right
    return r

def count_range(root, lo, hi):
    if hi < lo:
        return 0
    return count_leq(root, hi) - rank(root, lo)      # (# keys <= hi) - (# keys < lo)
```

Both descents are O(h). After deleting 3 the keys are 1, 4, 6, 7, 8, 10, 13, 14. `count_leq(root, 12)`: at 8, add 4 + 1 (r = 5), go right; at 10, add 0 + 1 (r = 6), go right; at 14 and 13, go left; result 6. `rank(root, 5)`: at 8 go left; at 4, add 1 + 1 (r = 2), go right; at 6 go left to `None`; result 2. So **4** keys lie in [5, 12]: 6, 7, 8, 10.

</details>

**7.9 ★★ Leaves of a random BST.** Insert the keys 1 to n (n ≥ 2) in uniformly random order. Using the ancestor rule of Section 7.3, show that key i is a leaf exactly when its neighbours in rank, i − 1 and i + 1 (those that exist), are both inserted before it. Conclude that the expected number of leaves is (n + 1)/3.

<details>
<summary>Hint</summary>

If i has any descendant j < i, then i is an ancestor of j, so i was inserted first among the keys j to i. What does that say about i − 1?

</details>

<details>
<summary>Solution</summary>

By the ancestor rule, i is an ancestor of j exactly when i is the first key inserted among those between j and i inclusive. If j < i, that range contains i − 1, so i must arrive before i − 1. Conversely, if i arrives before i − 1, then i is first in the two-key range {i − 1, i}, so i − 1 is a descendant of i. Hence i has a descendant on its left side **iff** i arrives before i − 1, and symmetrically on its right side iff i arrives before i + 1. So i is a leaf exactly when every existing neighbour arrives before it.

For 2 ≤ i ≤ n − 1, i is a leaf when it is the last of the three keys i − 1, i, i + 1 to arrive. In a random order each of the three is equally likely to be last: probability 1/3. For i = 1 and i = n there is one neighbour, and the probability is 1/2. By linearity of expectation:

E[leaves] = (n − 2) · 1/3 + 2 · 1/2 = (n − 2)/3 + 1 = **(n + 1)/3**

So about a third of the nodes in a random BST are leaves; in a perfect tree it is about half. Simulation agrees: 20,000 random trees on 50 keys average 17.0 leaves, and (50 + 1)/3 = 17.

</details>

---

## Where this connects

- [Chapter 8: Self-Balancing Trees](ch08-self-balancing-trees.md). What to do when this degrades to a linked list
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md). Making a BST persistent, so old versions survive updates
