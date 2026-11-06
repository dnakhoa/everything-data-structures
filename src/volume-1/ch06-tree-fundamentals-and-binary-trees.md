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

### Iterative Traversals with an Explicit Stack

The recursive traversals keep their bookkeeping on the call stack, one frame per level, so they need O(h) stack space. On a degenerate tree h is n − 1, and CPython's default recursion limit of 1000 frames means the recursive `inorder` raises `RecursionError` on a chain of about a thousand nodes. In C the same code overflows the thread's stack. Moving the stack into a list fixes this without changing the asymptotics: still O(n) time and O(h) space, but the space is ordinary heap memory.

**Preorder** is the easiest: pop a node, visit it, push its children. Push the right child first so that the left one is popped first.

```python
def preorder_iter(root):
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        visit(node)
        if node.right: stack.append(node.right)   # pushed first, popped second
        if node.left:  stack.append(node.left)
```

(Replace the stack with a queue, append left before right, and this becomes `level_order`. Depth-first and breadth-first differ only in the container.)

**Inorder** cannot visit a node when it first meets it; it has to go down the left side first and come back. The stack holds exactly the nodes whose left subtree is in progress and which have not been visited yet:

```python
def inorder_iter(root):
    stack, node = [], root
    while stack or node:
        while node:                 # run down the left spine, saving the path
            stack.append(node)
            node = node.left
        node = stack.pop()          # leftmost node not yet visited
        visit(node)
        node = node.right           # then its right subtree
```

On the tree 4 (children 2 and 5), 2 (children 1 and 3):

```
push 4, 2, 1          stack [4, 2, 1]
pop 1, visit 1        1 has no right child
pop 2, visit 2        go to 2.right = 3: push 3, stack [4, 3]
pop 3, visit 3        stack [4]
pop 4, visit 4        go to 4.right = 5: push 5, stack [5]
pop 5, visit 5        stack empty, node None: done        output 1 2 3 4 5
```

Every node is pushed once and popped once, so the whole traversal is O(n) and the stack never holds more than h + 1 nodes. Split the loop at `visit` and you have an iterator whose `next()` is amortized O(1): this is the standard way to iterate over a BST without parent pointers (Chapter 7, Section 7.4).

**Postorder** is the hardest, because the traversal comes back up to each node twice: once from its left subtree (when it must go right instead of visiting) and once from its right subtree. Remember the last node visited to tell the two apart:

```python
def postorder_iter(root):
    stack, node, last = [], root, None
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        top = stack[-1]
        if top.right and top.right is not last:
            node = top.right        # right subtree not done yet: go there first
        else:
            visit(top)              # both subtrees done
            last = stack.pop()
```

If `top` has a right child and we did not just finish it, we are coming back from the left, so we descend right. Otherwise both subtrees are done (the right one was the last thing visited, or there is none), and `top` is visited. A common shortcut runs preorder with the children pushed in the opposite order (root, right, left) and reverses the output. That is correct, but it holds all n results before producing the first one, so it is no use as a streaming iterator.

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

## 6.7 The Recursive Tree Function Pattern

Many questions about a binary tree have the same shape: the answer for a node can be computed from the answers for its two children. Height, size, sum of keys, "is it balanced", "is it a BST", "how long is the longest path". The pattern is a single **postorder** function that returns, for each subtree, a tuple of everything the parent will need:

1. Decide what the parent needs to know about a subtree. Sometimes that is more than the final answer.
2. Return that tuple for the empty tree (the base case).
3. For a node, recurse on both children, then combine their tuples and the node itself into the node's tuple.

Correctness is a direct induction on the tree: if the two recursive calls return correct tuples for the children's subtrees, the combine step produces a correct tuple for the node's subtree. Cost: every node is visited once and the combine step is O(1), so the whole pass is O(n) time and O(h) stack.

**Example: height, size and diameter in one pass.** The *diameter* is the number of edges on the longest path between any two nodes. That path bends at exactly one node, its highest, and the longest path bending at a node goes down to the deepest point in each of its subtrees: left height + right height + 2 edges (counting an empty subtree's height as −1). But the longest path in the whole tree need not bend at the root, so the parent needs two things from each child: the height (a path the parent can extend) and the best diameter found so far (a finished answer it can only compare against).

```python
def summary(node):
    """(height, size, diameter) of the subtree. Height of an empty tree is -1."""
    if node is None:
        return -1, 0, 0
    lh, ls, ld = summary(node.left)
    rh, rs, rd = summary(node.right)
    through = lh + rh + 2           # longest path that bends at this node
    return 1 + max(lh, rh), 1 + ls + rs, max(ld, rd, through)
```

On this tree the longest path, 5-3-2-4-6, does not touch the root:

```
          1                 node   (height, size, diameter)
         /                  5      (0, 1, 0)
        2                   3      (1, 2, 1)     through = 0 + (-1) + 2
       / \                  6      (0, 1, 0)
      3   4                 4      (1, 2, 1)
     /     \                2      (2, 5, 4)     through = 1 + 1 + 2
    5       6               1      (3, 6, 4)     through = 2 + (-1) + 2 = 3 < 4
```

The tempting alternative, calling a separate `height()` at every node to compute `through`, gives the same answer but recomputes each subtree's height once per ancestor: O(n²) on a long chain. Returning the height alongside the answer is what makes the pass linear. Exercise 6.5 uses the same idea for balance checking, and Chapter 7, Section 7.7 maintains subtree sizes in a BST this way.

This is how compilers compute *synthesized attributes* (a type or constant value for each expression node, from its children's), how `du` totals directory sizes, and how dynamic programming on trees is usually written.

## 6.8 Reconstructing a Tree from Traversals

One traversal sequence does not determine a binary tree: the keys 1, 2, 3 in inorder could come from five different shapes. Two traversals can, if one of them is **inorder** and the keys are distinct.

**Preorder + inorder.** The first preorder key is the root. Find it in the inorder sequence: the keys to its left form the left subtree and the keys to its right form the right subtree. In preorder the root is followed by the whole left subtree and then the whole right subtree, so the next keys in preorder belong to the left subtree, and their count is known from the inorder split. Recurse on each side. Since every step is forced, the tree is unique.

With preorder `A B D E C F` and inorder `D B E A F C`: the root is A, with `D B E` on its left and `F C` on its right. The left subtree's preorder is `B D E`, so its root is B, with D left of B and E right of it in inorder. The right subtree's preorder is `C F`; F is left of C in inorder, so F is C's left child:

```
        A
       / \
      B   C
     / \  /
    D  E F
```

As code, a position map makes each split O(1), and a single iterator over the preorder sequence is enough because the recursion builds nodes in exactly preorder order (root, then all of the left subtree, then the right):

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

This is O(n) time. Searching the inorder list for each root instead of using `pos` costs O(n log n) on a balanced tree but O(n²) on a chain. Postorder + inorder works the same way, with the root at the *end* (Exercise 6.3), and so does level order + inorder. Duplicate keys break all of these, because the root's position in inorder is no longer determined.

**Preorder + postorder is not enough in general.** Both sequences put a node next to its subtree, but neither says on which side a lone child hangs. The tree "1 with left child 2" and the tree "1 with right child 2" both have preorder `1 2` and postorder `2 1`. In general, if k nodes have exactly one child, all 2^k ways of choosing their sides give the same pair of sequences. Inorder is what separates them (`2 1` versus `1 2`). For a *full* binary tree, where every node has 0 or 2 children, the ambiguity cannot arise and preorder + postorder does determine the tree: the key after the root in preorder is the left child, and its position in postorder marks where the left subtree ends.

## 6.9 Serialization and Deserialization

Writing a tree to a file, a socket or a cache, and reading back the identical tree, needs a flat format that records the **shape** as well as the keys. Section 6.8 used two traversals for that; a single traversal is enough if it also writes a marker for every empty child.

**Preorder with null markers:**

```python
def serialize(node, out):
    if node is None:
        out.append('#')
        return
    out.append(str(node.key))
    serialize(node.left, out)
    serialize(node.right, out)

def deserialize(tokens):
    it = iter(tokens)

    def go():
        tok = next(it)
        if tok == '#':
            return None
        node = Node(tok)             # keys come back as strings
        node.left = go()             # the left subtree's tokens come next...
        node.right = go()            # ...then the right subtree's
        return node

    return go()
```

The tree of Section 6.8 serializes as `A B D # # E # # C F # # #`. `deserialize` reads the tokens in the order `serialize` wrote them, and by induction each call to `go` consumes exactly the tokens written for one subtree: a `#` ends a branch, so no sizes or end markers are needed. A tree with n nodes has n + 1 empty child slots (2n pointer fields, n − 1 of them used by edges), so the output is n keys plus n + 1 markers, and both directions are O(n). Unlike Section 6.8, duplicate keys are fine. Keys are written with `str` and read back as strings; a real format must encode keys so that they round-trip with their type and cannot be confused with the marker or the separator (escaping, or a length prefix).

**Other choices.** Level order with null markers is the format LeetCode uses (`[1,2,3,null,null,4,5]`, with trailing nulls dropped); it can be read back with a queue and has no recursion depth problem. Inorder with markers does **not** work: `# A # B #` is both "A with right child B" and "B with left child A", because inorder does not say which key is the parent. For a complete tree, the array layout of Section 6.5 needs no markers at all. And the markers cost little: writing 1 for a node and 0 for an empty slot in preorder records any shape in 2n + 1 bits. That is close to optimal, since there are C(2n, n)/(n + 1) binary tree shapes with n nodes (the Catalan number), roughly 4^n / n^1.5 of them, so any encoding needs about 2n bits. Succinct tree representations (Jacobson, 1989) build on such bit sequences, adding small indexes so that parent and child can be found without decoding the whole tree.

## 6.10 Expression Trees

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

## 6.11 Binary Space Partitioning Trees

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

## 6.12 Historical Context

Trees as mathematical structures predate computers. Graph theory, including trees, was studied in the 19th century by Kirchhoff, Cayley, and others. Arthur Cayley (1857) enumerated rooted trees, and in 1889 published what we now call "Cayley's formula": there are n^(n-2) labeled trees on n nodes.

The binary tree became central to computer science through:
- Syntax trees in compilers (1950s)
- Binary search trees (1960s)
- Balanced tree variants (1970s)
- B-trees for databases (1970s)

Knuth's *The Art of Computer Programming*, Volume 1 (1968), Section 2.3.1, gives inorder traversal with an explicit stack as Algorithm T. The bottom-up computation of Section 6.7 was formalized for compilers in Knuth's "Semantics of Context-Free Languages" (1968), which introduced synthesized and inherited attributes. Guy Jacobson's "Space-efficient static trees and graphs" (FOCS 1989) started the study of succinct trees that use about 2n bits for the shape.

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

**6.3 ★★ Rebuild a tree from postorder and inorder.** A binary tree with distinct keys has postorder `7 4 2 5 8 6 3 1` and inorder `4 7 2 1 5 3 8 6`. Draw the tree and give its preorder. Then adapt `build` from Section 6.8 to take postorder instead of preorder.

<details>
<summary>Hint</summary>

The last postorder key is the root. Read postorder backwards and it lists the root, then the whole right subtree, then the whole left subtree.

</details>

<details>
<summary>Solution</summary>

Root is 1 (last in postorder). In the inorder sequence, `4 7 2` is left of 1 and `5 3 8 6` is right of it. The left subtree has 3 keys, so it owns the first 3 postorder keys, `7 4 2`, and the right subtree owns `5 8 6 3`.

- Left part: postorder `7 4 2`, root 2. Inorder `4 7` lies left of 2, so 2 has only a left subtree, with postorder `7 4`: its root is 4, and 7 is right of 4 in inorder, so 7 is 4's right child.
- Right part: postorder `5 8 6 3`, root 3. Inorder `5` is left of 3 and `8 6` is right. So 5 is 3's left child; the right subtree has postorder `8 6`, root 6, with 8 to its left in inorder, so 8 is 6's left child.

```
          1
        /   \
       2     3
      /     / \
     4     5   6
      \       /
       7     8
```

Preorder: **1 2 4 7 3 5 6 8**.

In code, walk the postorder sequence backwards and build the right subtree before the left, because that is the order reversed postorder lists them in:

```python
def build_post(postorder, inorder):
    pos = {key: i for i, key in enumerate(inorder)}
    it = reversed(postorder)           # root, right subtree, left subtree

    def go(lo, hi):
        if lo >= hi:
            return None
        node = Node(next(it))
        mid = pos[node.key]
        node.right = go(mid + 1, hi)   # right first
        node.left = go(lo, mid)
        return node

    return go(0, len(inorder))
```

Building the left subtree first would be wrong: the next key from the reversed iterator is the root of the *right* subtree. Like `build`, this is O(n).

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

**6.6 ★★ Evaluate and print an expression tree.** Using the node layout from this chapter (operators at internal nodes, numbers at leaves), write `evaluate(node)` and `to_infix(node)`, where `to_infix` adds the parentheses that Section 6.10 says plain inorder is missing. On the tree for `(3 + 4) * (2 - 1)` they should return `7` and `((3 + 4) * (2 - 1))`. Which traversal order does each function use?

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

**6.8 ★★ Serialize a BST without markers.** Section 6.9 needs n + 1 null markers to record a tree's shape. For a binary search tree (Chapter 7) the plain preorder sequence of keys is enough. (a) Show that inserting the keys of a BST's preorder sequence, in that order, into an empty BST rebuilds exactly the same tree. (b) That takes O(nh) time. Write an O(n) deserializer instead, and rebuild the tree with preorder `8 3 1 6 4 7 10 14 13`.

<details>
<summary>Hint</summary>

For (b), pass down the open interval of keys that may appear in the current subtree, as in the BST validator of Chapter 7, Section 7.6. The next preorder key belongs to the current subtree exactly when it falls in that interval.

</details>

<details>
<summary>Solution</summary>

(a) Preorder lists every node after all of its ancestors. So when key x is inserted, all of x's ancestors in the original tree are already present, and by induction they sit in their original positions. The search for x starts at the root and at each node takes the same branch it would take in the original tree, so it passes through x's ancestors in order and ends at x's original parent, whose child slot on x's side is still empty because x's descendants come after x in preorder. So x lands in its original position.

(b) The bounds tell each call when its subtree has ended, so no markers are needed:

```python
def bst_from_preorder(keys):
    i = 0

    def go(lo, hi):                       # build the subtree whose keys lie in (lo, hi)
        nonlocal i
        if i == len(keys) or not (lo < keys[i] < hi):
            return None
        node = Node(keys[i])
        i += 1
        node.left = go(lo, node.key)
        node.right = go(node.key, hi)
        return node

    return go(float('-inf'), float('inf'))
```

Each call either consumes a key or returns `None` at once, and each node makes two calls, so there are at most 2n + 1 calls: O(n). On `8 3 1 6 4 7 10 14 13`: 8 is the root; 3 is in (−∞, 8), so it is 8's left child; 1 is in (−∞, 3), left of 3; 6 is not in (−∞, 1) or (1, 3), so 1 and its subtree end and 6 becomes 3's right child, in (3, 8); 4 and 7 become 6's children; 10 fails every interval below 8, so it becomes 8's right child; 14 is 10's right child and 13 is 14's left child. That is the example tree of Chapter 7, Section 7.1.

The saving is real: the shape of a BST is fixed by its keys and the order they were inserted in, and preorder is one order that reproduces it.

</details>

**6.9 ★★ The largest BST inside a binary tree.** Using the pattern of Section 6.7, write a function that returns the number of nodes in the largest subtree (a node together with all its descendants) that satisfies the BST property, in O(n) time. What tuple does each call return?

<details>
<summary>Hint</summary>

A node's subtree is a BST when both children's subtrees are BSTs, the left subtree's maximum is smaller than the node's key, and the right subtree's minimum is larger. So each call must report whether it is a BST, its size, its minimum and maximum, and the best answer found inside it.

</details>

<details>
<summary>Solution</summary>

```python
def bst_info(node):
    """(size if this subtree is a BST else -1, min key, max key, largest BST size inside)."""
    if node is None:
        return 0, None, None, 0
    ls, lmin, lmax, lbest = bst_info(node.left)
    rs, rmin, rmax, rbest = bst_info(node.right)
    if (ls >= 0 and rs >= 0
            and (lmax is None or lmax < node.key)
            and (rmin is None or node.key < rmin)):
        size = ls + rs + 1
        lo = lmin if lmin is not None else node.key
        hi = rmax if rmax is not None else node.key
        return size, lo, hi, size
    return -1, None, None, max(lbest, rbest)

def largest_bst(root):
    return bst_info(root)[3]
```

The tuple carries two kinds of information, as in `summary`: things the parent combines (whether the subtree is a BST, its size, its key range) and a finished answer it only compares (the best size inside). A subtree that is not a BST cannot be part of a larger BST, so its min and max are never needed and are returned as `None`. Each node is visited once with O(1) work: O(n) time, O(h) stack. Checking each node with a separate validator instead would cost O(n) per node, O(n²) in total.

</details>

---

## Where this connects

- [Chapter 7: Binary Search Trees](ch07-binary-search-trees.md). Adding an ordering invariant to the tree
- [Chapter 20: Data Structure Design Patterns](../volume-3/ch20-data-structure-design-patterns.md). The composite and iterator patterns these traversals exemplify
