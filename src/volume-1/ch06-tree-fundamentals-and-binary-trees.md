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
             /     |
            I      J
              |
             (I is descendant of E, B, A; ancestor of itself)
```

**Key Terms:**
- **Root**: The node with no parent (A)
- **Parent**: Node with children below it (B is parent of E and F)
- **Child**: Node with parent above it (E and F are children of B)
- **Sibling**: Nodes with same parent (E and F are siblings)
- **Leaf**: Node with no children (I, G, H, J)
- **Internal node**: Node with at least one child (A, B, C, D, F)
- **Depth**: Number of edges from root to node (I has depth 3)
- **Height**: Number of edges on longest path from node to leaf
- **Level**: All nodes at same depth
- **Path**: Sequence of nodes connected by edges
- **Subtree**: Node and all its descendants

## 6.3 Tree Properties

For a tree with n nodes:
- Exactly n-1 edges (each node except root has one edge to its parent)
- A tree with maximum nodes for a given height is "complete"
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

Trees as mathematical structures predate computers. Graph theory, including trees, was studied in the 19th century by Kirchhoff, Cayley, and others. Arthur Cayley (1857) enumerated rooted trees, establishing what we now call "Cayley's formula": there are n^(n-1) labeled trees on n nodes.

The binary tree became central to computer science through:
- Syntax trees in compilers (1950s)
- Binary search trees (1960s)
- Balanced tree variants (1970s)
- B-trees for databases (1970s)

---

## Where this connects

- [Chapter 7: Binary Search Trees](ch07-binary-search-trees.md) — adding an ordering invariant to the tree
- [Chapter 20: Data Structure Design Patterns](../volume-3/ch20-data-structure-design-patterns.md) — the composite and iterator patterns these traversals exemplify
