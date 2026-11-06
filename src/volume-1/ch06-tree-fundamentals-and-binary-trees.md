# Chapter 6: Tree Fundamentals and Binary Trees

## 6.1 The Tree Abstraction

A tree is a hierarchical data structure consisting of nodes connected by edges, with a single root node from which all other nodes are reachable. Trees model many natural hierarchies: organizational charts, file systems, family genealogies, and evolutionary relationships.

**Formal Definition:**
A tree T is a connected acyclic graph. Equivalently, a tree is a set of nodes where:
- There is a distinguished root node r
- Every node (except r) has exactly one parent
- There is a unique path from r to any node

## 6.2 Tree Terminology

```
                    A (Root, Depth 0)
                   /|\
                  / | \
                 B  C  D
                /|  |   \
               / |  |    \
              E  F  G     H
             /   |
            I    J
              |
             (I is descendant of E, B, A; ancestor of itself)
```

**Key Terms:**
- **Root**: The node with no parent (A)
- **Parent**: Node with children below it (B is parent of E and F)
- **Child**: Node with parent above it (E and F are children of B)
- **Sibling**: Nodes with same parent (E and F are siblings)
- **Leaf**: Node with no children (I, G, H, J)
- **Internal node**: Node with at least one child (A, B, C, D, E, F)
- **Depth**: Number of edges from root to node (I has depth 3)
- **Height**: Number of edges on longest path from node to leaf
- **Level**: All nodes at same depth
- **Path**: Sequence of nodes connected by edges
- **Subtree**: Node and all its descendants

## 6.3 Tree Properties

For a tree with n nodes:
- Exactly n-1 edges (each node except root has one edge to its parent)
- A binary tree with maximum nodes for a given height is "perfect"
- A tree with minimum height for a given n is "balanced"

**The Handshaking Lemma:**
In any tree: Σ degree(v) = 2(n-1)
This follows because each of the n-1 edges contributes 2 to the degree sum.

## 6.4 Binary Trees

A binary tree is a tree where each node has at most two children, distinguished as left and right.

```c
struct TreeNode {
    element_type data;
    struct TreeNode *left;
    struct TreeNode *right;
};
```

### Types of Binary Trees

**Full (Proper) Binary Tree:** Every node has 0 or 2 children:
```
       ○
      / \
     ○   ○
    / \
   ○   ○
```

**Complete Binary Tree:** All levels filled except possibly the last, filled left to right:
```
       ○
      / \
     ○   ○
    /\  /\
   ○ ○ ○  ○
```

**Perfect Binary Tree:** All internal nodes have 2 children; all leaves at same level:
```
       ○
      / \
     ○   ○
    /\  /\
   ○ ○ ○ ○
```

**Balanced Binary Tree:** Height of left and right subtrees differs by at most 1:
```
       ○                    ○
      / \                  / \
     ○   ○    is balanced  ○   ○
    /                         \
   ○                           ○
```

## 6.5 Binary Tree Representations

### Pointer-Based Representation

```c
struct Node {
    element_type data;
    struct Node *left;
    struct Node *right;
};
```

Simple, natural, widely used.

### Array Representation (For Complete Trees)

For complete binary trees, store nodes level-by-level in an array:

```
Array indices:
       0
      / \
     1   2
    /\  /\
   3  4 5  6

Array: [A, B, C, D, E, F, G]

Parent(i)  = (i - 1) / 2
Left(i)    = 2 * i + 1
Right(i)   = 2 * i + 2
```

This representation is space-efficient for complete trees and is used for heaps.

### Left-Child Right-Sibling Representation

Convert any general tree to binary tree:

```c
struct GeneralNode {
    element_type data;
    struct GeneralNode *first_child;
    struct GeneralNode *next_sibling;
};
```

The binary tree has:
- left pointer → first child
- right pointer → next sibling

## 6.6 Tree Traversals

Traversal is visiting each node in a systematic order.

### Preorder (Root, Left, Right)

```python
def preorder(node):
    if node is None: return
    visit(node)          # Process root first
    preorder(node.left)   # Then all left subtree
    preorder(node.right)  # Then all right subtree
```

Use cases: Copy tree, prefix notation, directory listing

### Inorder (Left, Root, Right)

```python
def inorder(node):
    if node is None: return
    inorder(node.left)    # Left subtree
    visit(node)           # Process root
    inorder(node.right)   # Right subtree
```

Use cases: BST in sorted order, infix expression evaluation

### Postorder (Left, Right, Root)

```python
def postorder(node):
    if node is None: return
    postorder(node.left)   # Left subtree
    postorder(node.right)  # Right subtree
    visit(node)            # Process root last
```

Use cases: Delete tree, postfix evaluation, computing directory sizes

### Level Order (Breadth-First)

```python
from collections import deque

def level_order(root):
    if root is None: return
    queue = deque([root])

    while queue:
        node = queue.popleft()
        visit(node)
        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)
```

Use cases: Shortest path in unweighted graph, level-by-level processing

### Morris Traversal (Threaded Binary Tree)

O(1) space traversal using existing tree structure:

```python
def morris_inorder(root):
    current = root
    while current:
        if current.left is None:
            visit(current)
            current = current.right
        else:
            # Find inorder predecessor (rightmost in left subtree)
            pre = current.left
            while pre.right and pre.right != current:
                pre = pre.right

            if pre.right is None:
                pre.right = current  # Create thread
                current = current.left
            else:
                pre.right = None     # Remove thread
                visit(current)
                current = current.right
```

## 6.7 Expression Trees

Binary expression trees represent arithmetic expressions:

```
Expression: (3 + 4) * (2 - 1)

        *
       / \
      +   -
     / \ / \
    3  4 2  1

Preorder (prefix):    * + 3 4 - 2 1
Inorder (infix):      3 + 4 * 2 - 1  (needs parentheses for correctness)
Postorder (postfix):  3 4 + 2 1 - *
```

## 6.8 Binary Space Partitioning Trees

BSP trees recursively divide space with hyperplanes:

```
        │                    │
   ─────┼─────        ───────┼──────
        │    partition       │    partition
   ─────┼─────        ───────┼──────
        │                    │
```

Used in:
- 3D graphics (visibility determination)
- Ray tracing
- Collision detection
- CAD systems

## 6.9 Historical Context

Trees as mathematical structures predate computers. Graph theory, including trees, was studied in the 19th century by Kirchhoff, Cayley, and others. Arthur Cayley (1857) enumerated rooted trees, and in 1889 published what we now call "Cayley's formula": there are n^(n-2) labeled trees on n nodes.

The binary tree became central to computer science through:
- Syntax trees in compilers (1950s)
- Binary search trees (1960s)
- Balanced tree variants (1970s)
- B-trees for databases (1970s)

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**6.1 ★ Read the terminology tree.** Use the tree in Section 6.2 (A has children B, C, D; B has E and F; C has G; D has H; E has I; F has J). Give (a) the height of the whole tree, (b) the height of B, (c) the depth of J, (d) the number of edges, and (e) the sum of the degrees of all nodes, treating the tree as an undirected graph. Check (d) and (e) against Section 6.3.

<details>
<summary>Solution</summary>

(a) The longest root-to-leaf paths are A→B→E→I and A→B→F→J, each 3 edges, so the height is **3**.

(b) From B the longest downward path is B→E→I (or B→F→J): height **2**.

(c) J is reached by A→B→F→J: depth **3**.

(d) There are 10 nodes, so **9** edges. Counting directly: every node except A has exactly one edge to its parent, which is 9.

(e) Degrees (parent edge plus child edges): A 3, B 3, C 2, D 2, E 2, F 2, G 1, H 1, I 1, J 1. The sum is **18** = 2 × 9 = 2(n − 1), as the handshaking lemma says.

</details>

**6.2 ★ Four traversals.** Write the preorder, inorder, postorder and level-order sequences for this tree.

```
          F
        /   \
       B     G
      / \     \
     A   D     I
        / \   /
       C   E H
```

<details>
<summary>Solution</summary>

- **Preorder** (root, left, right): F B A D C E G I H
- **Inorder** (left, root, right): A B C D E F G H I
- **Postorder** (left, right, root): A C E D B H I G F
- **Level order**: F B G A D I C E H

The inorder sequence comes out alphabetical because this tree happens to obey the BST property of Chapter 7. Preorder always starts with the root and postorder always ends with it, which is the fact the next exercise relies on.

</details>

**6.3 ★★ Rebuild a tree from two traversals.** A binary tree with distinct keys has preorder `1 2 4 7 3 5 6 8` and inorder `4 7 2 1 5 3 8 6`. Draw the tree and give its postorder. Then show that preorder plus postorder is *not* always enough to determine a binary tree.

<details>
<summary>Hint</summary>

The first preorder key is the root. Find it in the inorder sequence: everything to its left is the left subtree, everything to its right is the right subtree. Recurse.

</details>

<details>
<summary>Solution</summary>

Root is 1. In the inorder sequence, `4 7 2` is left of 1 and `5 3 8 6` is right of it.

- Left part: the next preorder keys are `2 4 7`, so its root is 2. Inorder `4 7` lies left of 2, so 2 has only a left subtree. Its root is 4 (next in preorder), and 7 is right of 4 in inorder, so 7 is 4's right child.
- Right part: preorder `3 5 6 8`, root 3. Inorder `5` is left of 3 and `8 6` is right. So 5 is 3's left child; the right subtree has root 6 (next in preorder) with 8 to its left in inorder, so 8 is 6's left child.

```
          1
        /   \
       2     3
      /     / \
     4     5   6
      \       /
       7     8
```

Postorder: **7 4 2 5 8 6 3 1**.

The same procedure as code, O(n) with a position map:

```python
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None

def build(preorder, inorder):
    pos = {key: i for i, key in enumerate(inorder)}
    it = iter(preorder)

    def go(lo, hi):              # build the subtree whose keys are inorder[lo:hi]
        if lo >= hi:
            return None
        node = Node(next(it))    # next preorder key is this subtree's root
        mid = pos[node.key]
        node.left = go(lo, mid)
        node.right = go(mid + 1, hi)
        return node

    return go(0, len(inorder))
```

Preorder plus postorder fails when a node has exactly one child. The tree "1 with left child 2" and the tree "1 with right child 2" both have preorder `1 2` and postorder `2 1`. Inorder is what distinguishes them (`2 1` versus `1 2`). For a full binary tree (every node has 0 or 2 children) preorder plus postorder is enough, because that ambiguity cannot arise.

</details>

**6.4 ★★ Array layout.** A complete binary tree with n = 12 nodes is stored in an array using the formulas in Section 6.5. (a) Which indices hold leaves? (b) Which internal node has only one child, and what is it? (c) Prove that for any n, the leaves are exactly the indices ⌊n/2⌋ through n − 1. (d) If you used the same formulas for a right-leaning chain of 5 nodes, how large must the array be?

<details>
<summary>Hint</summary>

A node at index i is a leaf exactly when its left child index 2i + 1 is past the end of the array.

</details>

<details>
<summary>Solution</summary>

(a) Index i is a leaf when 2i + 1 ≥ 12, that is i ≥ 5.5, so indices **6 through 11** are leaves and 0 through 5 are internal.

(b) Index 5 has left child 2·5 + 1 = 11 (present) and right child 12 (absent). So **index 5 has one child, index 11**. In a complete tree at most one node can be in this position.

(c) i is internal iff 2i + 1 ≤ n − 1, iff i ≤ (n − 2)/2, iff i ≤ ⌊n/2⌋ − 1. So the internal nodes are 0 through ⌊n/2⌋ − 1 and the leaves are ⌊n/2⌋ through n − 1. This is why `build_heap` in Chapter 9 starts its loop at n/2 − 1: every larger index is a leaf and already a valid heap.

(d) Following right children from the root visits indices 0, 2, 6, 14, 30 (each is 2i + 2). The array needs **31** slots to hold 5 nodes. In general a chain of height h needs 2^(h+1) − 1 slots, which is why the array layout is reserved for complete trees.

</details>

**6.5 ★★ Find the bug.** The balanced-tree definition in Section 6.4 must hold at *every* node. This check is meant to test it:

```python
def height(node):
    if node is None:
        return -1
    return 1 + max(height(node.left), height(node.right))

def is_balanced(node):
    if node is None:
        return True
    return abs(height(node.left) - height(node.right)) <= 1
```

Give a tree on which it returns the wrong answer, then write a correct version that runs in O(n).

<details>
<summary>Hint</summary>

It only looks at the root. Build a tree whose root is fine but whose children are not. For the O(n) version, compute heights and balance in the same pass.

</details>

<details>
<summary>Solution</summary>

The function compares the two subtree heights at the root and never recurses. This tree has left and right subtrees of height 2 each, so it returns `True`, but node 2 has a left subtree of height 1 and an empty right subtree (height −1), a difference of 2:

```
        1
       / \
      2   3
     /     \
    4       5
   /         \
  6           7
```

Adding the recursive calls (`... and is_balanced(node.left) and is_balanced(node.right)`) fixes correctness but recomputes heights at every level, which is O(n²) on a long chain. Returning the height and the verdict together is O(n), since each node is visited once:

```python
def balanced_height(node):
    """Height of the subtree, or None if any node in it is unbalanced."""
    if node is None:
        return -1
    lh = balanced_height(node.left)
    if lh is None:
        return None
    rh = balanced_height(node.right)
    if rh is None or abs(lh - rh) > 1:
        return None
    return 1 + max(lh, rh)

def is_balanced(node):
    return balanced_height(node) is not None
```

</details>

**6.6 ★★ Evaluate and print an expression tree.** Using the node layout from this chapter (operators at internal nodes, numbers at leaves), write `evaluate(node)` and `to_infix(node)`, where `to_infix` adds the parentheses that Section 6.7 says plain inorder is missing. On the tree for `(3 + 4) * (2 - 1)` they should return `7` and `((3 + 4) * (2 - 1))`. Which traversal order does each function use?

<details>
<summary>Solution</summary>

```python
def evaluate(node):
    if node.left is None and node.right is None:
        return node.key                    # a number
    a = evaluate(node.left)
    b = evaluate(node.right)
    if node.key == '+': return a + b
    if node.key == '-': return a - b
    if node.key == '*': return a * b
    if node.key == '/': return a / b
    raise ValueError(node.key)

def to_infix(node):
    if node.left is None and node.right is None:
        return str(node.key)
    return '(' + to_infix(node.left) + ' ' + node.key + ' ' + to_infix(node.right) + ')'
```

`evaluate` is a **postorder** traversal: both operands must be computed before the operator at the root can be applied, which is exactly how a stack machine runs `3 4 + 2 1 - *`. `to_infix` is an **inorder** traversal with a parenthesis emitted before the left subtree and after the right one.

The parentheses matter because two different trees can have the same plain inorder sequence. `8 - 3 - 2` is the inorder of both `((8 - 3) - 2)`, which is 3, and `(8 - (3 - 2))`, which is 7.

</details>

**6.7 ★★★ Why Morris traversal is linear.** The inner `while` loop of `morris_inorder` walks from `current.left` down the right pointers to find the predecessor. That walk can be long, and it happens twice per node with a left child. Prove that the total number of inner-loop steps over the whole traversal is at most 2(n − 1), so the traversal is O(n) time. Also argue that the tree is unchanged when the function returns.

<details>
<summary>Hint</summary>

Every step of the inner loop follows a real tree edge of the form (u, u.right). Ask: for how many different values of `current` can that particular edge be on the walk?

</details>

<details>
<summary>Solution</summary>

**Which edges a walk uses.** When `current` = c has a left child, the walk starts at c.left and follows right pointers. It stops at the node whose `right` is either `None` or a thread back to c, and it never follows that last pointer. So every step it takes is along a real tree edge (u, u.right), and those edges form the *right spine of c's left subtree*.

**Each edge belongs to one spine.** Take a tree edge (u, u.right). Walk up from u while the current node is a right child of its parent. You stop at a node w that is either the root or a left child of some parent c. If w is the root, the edge is on no left subtree's right spine. Otherwise the edge is on the right spine of c's left subtree and on no other, because that upward walk is deterministic. So each tree edge is charged to at most one c.

**Each spine is walked twice.** For a given c, the walk happens once on the first visit (creating the thread) and once when `current` returns to c through that thread (removing it). Both walks take the same edges.

So the inner loop takes at most 2 steps per tree edge, and there are n − 1 edges: **at most 2(n − 1) steps in total**. The outer loop moves `current` once per iteration, and each node becomes `current` at most twice (on arrival, and on return via its thread if it has a left child), so the outer loop is also O(n). Total: O(n) time, O(1) extra space.

**The tree is restored.** A thread is created only on the first visit to c (when the predecessor's `right` is `None`) and is removed on the second visit, before `current` moves to c.right. Every node with a left child is visited twice (traversal enters its left subtree and must come back through the thread to leave it), so every thread created is also removed. The bound is tight up to constants: for a root whose left subtree is a right-leaning chain of n − 1 nodes, the walks take 2(n − 2) steps.

</details>

---

## Where this connects

- [Chapter 7: Binary Search Trees](ch07-binary-search-trees.md). Adding an ordering invariant to the tree
- [Chapter 20: Data Structure Design Patterns](../volume-3/ch20-data-structure-design-patterns.md). The composite and iterator patterns these traversals exemplify
