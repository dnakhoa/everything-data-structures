# Chapter 8: Self-Balancing Trees

## 8.1 Why Balance Matters

Consider inserting keys in sorted order into a regular BST:

```
Insert 1, 2, 3, 4, 5, 6, 7:

     1
      \
       2
        \
         3
          \
           4
            \
             5
              \
               6
                \
                 7

Height = 7, Search = O(7)
```

Now consider the same in a balanced tree:

```
Same keys, balanced:

         4
       /   \
      2     6
     / \   / \
    1   3 5   7

Height = 3, Search = O(3)
```

The difference becomes dramatic at scale:
- n = 1,000,000
- Unbalanced height = 1,000,000 → worst case 1M comparisons
- Balanced height ≈ 20 → at most 20 comparisons

## 8.2 AVL Trees

AVL trees (Adelson-Velsky and Landis, 1962) were the first balanced BST, maintaining balance via height checks.

### The Balance Factor

```
balance_factor(node) = height(left) - height(right)

Allowed values: -1, 0, 1

AVL Tree (balanced):      Not AVL (unbalanced):
       4                        4
      / \                      /
     2   5                    2
    / \                        \
   1   3                        3
                              /
                             1
Height: -1                     -2
```

### Rotations

Rotations restructure the tree to restore balance.

**Right Rotation (for left-heavy):**
```
Before:                    After:
    z                         y
   / \                       / \
  y   T4        →           x   z
 / \                       / \ / \
x   T3                    T1 T2 T3 T4

Node z has balance factor -2 (left-heavy)
```

```c
Node* rotate_right(Node *z) {
    Node *y = z->left;
    Node *T3 = y->right;

    y->right = z;
    z->left = T3;

    // Update heights
    z->height = 1 + max(height(z->left), height(z->right));
    y->height = 1 + max(height(y->left), height(y->right));

    return y;
}
```

**Left Rotation (for right-heavy):**
```
Before:                    After:
    z                         y
   / \                       / \
  T1  y        →            z   x
     / \                   / \ / \
    T2  x                 T1 T2 T3 T4
```

**Left-Right Double Rotation:**
```
Before:                        After:
    z                           x
   / \                         / \
  y   T4        →             y   z
 / \                         / \ / \
T1  x                       T1 T2 T3 T4
   / \
  T2 T3
```

### AVL Insertion

1. Insert as in BST
2. Update heights
3. Check balance factors from inserted node up
4. If balance factor violates, rotate at first unbalanced node

```c
Node* insert_avl(Node *node, int key) {
    // Standard BST insert
    if (!node) return new_node(key);
    if (key < node->key) node->left = insert_avl(node->left, key);
    else if (key > node->key) node->right = insert_avl(node->right, key);
    else return node;  // Duplicate

    // Update height
    node->height = 1 + max(height(node->left), height(node->right));

    // Get balance factor
    int balance = get_balance(node);

    // Four cases
    // Left-Left
    if (balance > 1 && key < node->left->key)
        return rotate_right(node);

    // Right-Right
    if (balance < -1 && key > node->right->key)
        return rotate_left(node);

    // Left-Right
    if (balance > 1 && key > node->left->key) {
        node->left = rotate_left(node->left);
        return rotate_right(node);
    }

    // Right-Left
    if (balance < -1 && key < node->right->key) {
        node->right = rotate_right(node->right);
        return rotate_left(node);
    }

    return node;
}
```

### AVL Properties

- Height ≤ 1.44 log₂(n+1) (tight bound)
- Search, insert, delete: O(log n)
- Insert may require at most 2 rotations
- Delete may require up to O(log n) rotations
- Better for read-heavy workloads

## 8.3 Red-Black Trees

Red-black trees use color bits instead of heights, enabling simpler rebalancing.

### Red-Black Properties

1. Every node is either red or black
2. Root is black
3. All leaves (NIL) are black
4. Red nodes cannot have red children (no red-red)
5. Every path from a node to descendant leaves has the same number of black nodes

```
Valid Red-Black Tree:
            B(30)
           /      \
        R(10)    R(40)
        /  \     /   \
      B(5) B(20) B(35) B(50)

Path black counts (from any node):
30→5: B,R,B = 3 black nodes
30→20: B,R,B = 3 black nodes
30→35: B,R,B = 3 black nodes
30→50: B,R,B = 3 black nodes
```

### Why Properties Guarantee Balance

From property 5, all paths from root to leaves have the same black count. Combined with property 4 (no consecutive reds), the longest path is at most twice the shortest. Since shortest path has at least log₂(n+1) black nodes, the tree height is at most 2 × log₂(n+1) = O(log n).

### Rotations and Recoloring

Red-black operations are more complex but use fewer rotations than AVL.

**Insertion Cases:**
```
Case 1: Uncle is red
    Recolor parent, uncle to black, grandparent to red

Case 2: Uncle is black, triangle
    Rotate child up

Case 3: Uncle is black, line
    Rotate parent up
```

```c
void insert_rb(Node **root, int key) {
    // Standard BST insert
    Node *new = bst_insert(*root, key);
    new->color = RED;

    // Fix violations
    fix_violation(root, new);
}

void fix_violation(Node **root, Node *z) {
    Node *parent = NULL, *grandparent = NULL;

    while (z != *root && is_red(z) && parent != NULL) {
        parent = z->parent;
        grandparent = parent->parent;

        // Parent is left child
        if (parent == grandparent->left) {
            Node *uncle = grandparent->right;

            if (is_red(uncle)) {  // Case 1
                parent->color = BLACK;
                uncle->color = BLACK;
                grandparent->color = RED;
                z = grandparent;
            } else {
                if (z == parent->right) {  // Case 2
                    z = parent;
                    rotate_left(root, z);
                }
                // Case 3
                parent->color = BLACK;
                grandparent->color = RED;
                rotate_right(root, grandparent);
            }
        } else {  // Parent is right child (symmetric)
            // ... mirror cases
        }
    }
    (*root)->color = BLACK;
}
```

### AVL vs Red-Black Comparison

| Aspect | AVL | Red-Black |
|--------|-----|-----------|
| Balance criterion | Stricter | More relaxed |
| Tree height | ≤ 1.44 log₂(n) | ≤ 2 log₂(n) |
| Search performance | Better | Slightly worse |
| Insert performance | More rotations | Fewer rotations |
| Delete performance | More rotations | More rotations |
| Memory overhead | Height field | Color bit |
| Use case | Read-heavy | Write-heavy |

## 8.4 Splay Trees

Splay trees (Sleator and Tarjan, 1985) use a different strategy: instead of maintaining invariants, they "splay" accessed nodes to the root.

### The Splay Operation

When accessing a node, perform rotations to bring it to the root:
- **Zig**: Node is child of root
- **Zig-Zig**: Node and parent are both left/right children
- **Zig-Zag**: Node is left, parent is right (or vice versa)

```
Zig-Zig (left-left):
      g                    x
     / \                 / \
    p   T4      →      T1   p
   / \                     / \
  x   T3                  T2  g
 / \                         / \
T1  T2                     T3  T4

Zig-Zag (left-right):
    g                    x
   / \                 / \
  p   T4     →       p   g
 / \                 / \ / \
T1  x               T1 T2 T3 T4
   / \
  T2 T3
```

### Amortized Analysis

Using the potential method with potential = Σ log₂(size(i)), each splay operation costs O(log n) amortized.

Key property: Recently accessed elements are near the root (temporal locality). For repeated access to same element, splay trees are optimal.

### Splay Tree Properties

- O(log n) amortized for insert, delete, search
- O(log n) worst-case per operation
- No balance information needed (simpler implementation)
- Adaptive: good for locality of reference
- No guaranteed worst-case (unlike AVL, Red-Black)
- Can be made partially persistent

## 8.5 Scapegoat Trees

Scapegoat trees maintain balance by rebuilding subtrees when they become too unbalanced.

### Balance Criterion

A tree is α-weight-balanced if for every node:
size(child) ≤ α × size(node)

Typical α = 0.5 to 1 (0.5 = AVL-like strictness)

### Insertion

1. Insert as in BST
2. Walk back to root tracking path
3. If height > log_1/α (n), find scapegoat and rebuild

The scapegoat is not necessarily the deepest unbalanced node; any node on the path that restores balance works.

### Properties

- No rotations needed (simpler than AVL/Red-Black)
- O(log n) amortized insert/delete
- O(log n) worst-case search
- Simple to implement
- Good for systems where rotations are expensive

## 8.6 Treaps

Treaps combine BST with random heap priorities.

### Why Random Priorities Work

With random priorities:
- Expected height = O(log n)
- Probability of O(n) height = negligible
- No explicit balancing needed

```python
import random

class TreapNode:
    def __init__(self, key, priority=None):
        self.key = key
        self.priority = priority or random.random()
        self.left = None
        self.right = None

def treap_insert(root, node):
    if not root:
        return node

    if node.key < root.key:
        root.left = treap_insert(root.left, node)
        if root.left.priority < root.priority:
            root = rotate_right(root)
    else:
        root.right = treap_insert(root.right, node)
        if root.right.priority < root.priority:
            root = rotate_left(root)

    return root
```

## 8.7 Performance Comparison

| Tree Type | Search | Insert | Delete | Balance | Memory |
|-----------|--------|--------|--------|---------|--------|
| BST (unbalanced) | O(n) | O(n) | O(n) | None | Low |
| AVL | O(log n) | O(log n) | O(log n) | Strict | Height |
| Red-Black | O(log n) | O(log n) | O(log n) | Relaxed | 1 bit |
| Splay | O(log n)* | O(log n)* | O(log n)* | Amortized | None |
| Scapegoat | O(log n) | O(log n)* | O(log n)* | Rebuild | None |
| Treap | O(log n)* | O(log n)* | O(log n)* | Probabilistic | Priority |

*Amortized or expected

## 8.8 Real-World Usage

| Tree Type | Real-World Uses |
|-----------|----------------|
| Red-Black | Linux kernel (completely fair scheduler), Java's TreeMap/TreeSet, C++ STL (typically), Lua tables |
| AVL | Databases with frequent lookups, file systems |
| Splay | Network routing (LRU caches), memory allocators |
| Treap | Skip list alternative in some databases |
