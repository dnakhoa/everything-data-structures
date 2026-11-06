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

## 7.7 Applications of BSTs

- **Ordered maps**: Python dict (but actually hash-based), C++ map, Java TreeMap
- **Ordered sets**: C++ set, Java TreeSet (Python set is hash-based too)
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

**7.4 ★★ Find the bug.** This function is supposed to check the BST property:

```python
def is_bst(node):
    if node is None:
        return True
    if node.left and node.left.key >= node.key:
        return False
    if node.right and node.right.key <= node.key:
        return False
    return is_bst(node.left) and is_bst(node.right)
```

Give a tree that it wrongly accepts, explain why, and fix it.

<details>
<summary>Hint</summary>

Section 7.1 says *all* nodes in the left subtree are smaller, not just the left child.

</details>

<details>
<summary>Solution</summary>

It only compares each node with its direct children. This tree passes every local check (3 < 8, and 9 > 3) but is not a BST, because 9 sits in 8's left subtree:

```
      8
     /
    3
     \
      9
```

`bst_search(root, 9)` would go right from 8, find nothing, and report 9 missing even though it is in the tree.

The fix carries the open interval that every key in a subtree must fall in. Going left tightens the upper bound; going right tightens the lower bound:

```python
def is_bst(node, lo=None, hi=None):
    if node is None:
        return True
    if (lo is not None and node.key <= lo) or (hi is not None and node.key >= hi):
        return False
    return is_bst(node.left, lo, node.key) and is_bst(node.right, node.key, hi)
```

An equivalent check is an inorder traversal that verifies each key is larger than the previous one. Both are O(n).

</details>

**7.5 ★★ Successor without parent pointers.** Section 7.3 lists successor as an O(h) operation. Write `successor(root, key)` that returns the smallest key in the tree strictly greater than `key` (or `None`), in O(h) time and O(1) extra space, without parent pointers. `key` need not be in the tree. On the example tree in Section 7.1, what does it return for 7, 6, 5 and 14?

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

**7.6 ★★★ Range queries in O(h + k).** Section 7.8 says to use a BST when "range queries [are] needed". Write `range_keys(node, lo, hi, out)` that appends every key in [lo, hi] to `out` in sorted order. Then prove that it visits at most k + 2(h + 1) nodes, where k is the number of keys reported and h is the tree's height.

<details>
<summary>Hint</summary>

Do an inorder traversal, but skip a subtree when the BST property says it cannot contain any key in range. For the bound, show that every visited node whose key is *below* lo lies on the search path for lo.

</details>

<details>
<summary>Solution</summary>

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

It is an inorder traversal with pruning, so the output is sorted. A subtree is skipped only when every key in it is out of range: if node.key ≤ lo, its left subtree holds keys < lo; if node.key ≥ hi, its right subtree holds keys > hi. So every in-range key is reported.

**Bound.** Visited nodes are of three kinds: in range (exactly k of them), below lo, or above hi.

Take a visited node v with v.key < lo, and look at each step on the path from the root to v. If the step went *left* from u, the function only does that when lo < u.key, and the search for lo also goes left at u. If the step went *right* from u, then v is in u's right subtree, so u.key < v.key < lo, and the search for lo also goes right at u. Every step agrees with the search for lo, so v is on the search path for lo. That path has at most h + 1 nodes.

The symmetric argument puts every visited node above hi on the search path for hi, another h + 1 nodes at most. Total: at most **k + 2(h + 1)**, which is O(h + k). On a balanced tree that is O(log n + k): you pay for finding the two ends of the range plus one unit per answer, no matter how large n is. A hash table has no equivalent; it has to scan all n keys.

</details>

**7.7 ★ BST or hash table?** For each service, pick a hash table or a balanced BST and give the deciding reason. (a) A session store that maps random session tokens to user IDs; the only operations are insert, lookup by exact token, and delete. (b) A log index keyed by timestamp; the common query is "all events between 10:00 and 10:05". (c) A leaderboard that must answer "who has the next-highest score after mine?"

<details>
<summary>Solution</summary>

(a) **Hash table.** Only point queries, and no ordering is ever used. Expected O(1) beats O(log n), and random tokens hash well. A BST here pays for an ordering nobody reads.

(b) **Balanced BST** (or a B+ tree on disk, Chapter 10). A time-range query is the `range_keys` pattern of 7.6: O(log n + k). A hash table scatters adjacent timestamps across buckets, so it must scan everything.

(c) **Balanced BST** keyed by score. "Next-highest score" is the successor query of 7.5, O(log n). A hash table has no notion of "next" and would need an O(n) scan per query.

The pattern from Section 7.8: if any query involves order (next, previous, min, max, range, sorted iteration), the BST wins; if every query is an exact match, the hash table wins.

</details>

---

## Where this connects

- [Chapter 8: Self-Balancing Trees](ch08-self-balancing-trees.md). What to do when this degrades to a linked list
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md). Making a BST persistent, so old versions survive updates
