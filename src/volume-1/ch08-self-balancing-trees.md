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

<figure>
{{#include ../images/avl-rotation.svg}}
<figcaption>A right rotation. Three pointers change; the in-order sequence does not.</figcaption>
</figure>

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

Balance factor of root: +1     +2
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

Node z has balance factor +2 (left-heavy)
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
30→5: B,R,B = 2 black nodes
30→20: B,R,B = 2 black nodes
30→35: B,R,B = 2 black nodes
30→50: B,R,B = 2 black nodes
```

### Why Properties Guarantee Balance

From property 5, all paths from root to leaves have the same black count. Combined with property 4 (no consecutive reds), the longest path is at most twice the shortest. A subtree whose root has black-height bh contains at least 2^bh - 1 nodes, so the black-height of the root is at most log₂(n+1), and the tree height is at most 2 × log₂(n+1) = O(log n).

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
    while (z != *root && is_red(z) && is_red(z->parent)) {
        Node *parent = z->parent;
        Node *grandparent = parent->parent;

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
                    rotate_left(root, parent);
                    z = parent;
                    parent = z->parent;
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
| Delete performance | Up to O(log n) rotations | At most 3 rotations |
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
- O(n) worst case for a single operation
- No balance information needed (simpler implementation)
- Adaptive: good for locality of reference
- No guaranteed worst-case (unlike AVL, Red-Black)
- Can be made partially persistent

## 8.5 Scapegoat Trees

Scapegoat trees maintain balance by rebuilding subtrees when they become too unbalanced.

### Balance Criterion

A tree is α-weight-balanced if for every node:
size(child) ≤ α × size(node)

Typical α is strictly between 0.5 and 1 (α = 0.5 demands near-perfect balance; α close to 1 allows almost any shape)

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

<figure>
{{#include ../images/skip-list.svg}}
<figcaption>A skip list reaching the same O(log n) with coin flips instead of rotations.</figcaption>
</figure>

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
| Red-Black | Linux kernel (completely fair scheduler), Java's TreeMap/TreeSet, C++ STL (typically) |
| AVL | Databases with frequent lookups, file systems |
| Splay | Network routing (LRU caches), memory allocators |
| Treap | Skip list alternative in some databases |

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**8.1 ★ AVL insertion by hand.** Insert 10, 20, 30, 40, 50, 25 into an empty AVL tree using `insert_avl`. For each insertion that triggers a rotation, name the node where the imbalance is detected and which of the four cases applies. Draw the final tree.

<details>
<summary>Solution</summary>

Balance factor is height(left) − height(right), as in Section 8.2.

- **10, 20**: no imbalance. 10 has right child 20.
- **30**: path 10→20→30. At 10 the balance factor is −2 and 30 > 20 (the right child's key), so **Right-Right at 10**: `rotate_left(10)`. Tree: 20 with children 10 and 30.
- **40**: goes right of 30. Balance factors are −1 at 30 and −1 at 20. No rotation.
- **50**: path 20→30→40→50. 40 is at −1, 30 is at −2, and 50 > 40, so **Right-Right at 30**: `rotate_left(30)`. Tree: 20 with children 10 and 40; 40 has children 30 and 50.
- **25**: goes 20→40→30, left of 30. 30 is at +1, 40 is at +1, but 20 has a left subtree of height 0 and a right subtree of height 2 (edges), so −2. 25 < 40 (the right child's key), so **Right-Left at 20**: `rotate_right(40)` makes 30 the root of that subtree, then `rotate_left(20)` lifts 30 to the top.

```
          30
        /    \
      20      40
     /  \       \
   10    25      50
```

Every node now has balance factor −1, 0 or +1, and inorder is still 10 20 25 30 40 50. Three insertions caused rotations, and each was fixed at the *lowest* unbalanced ancestor with at most two rotations, as Section 8.2 says.

</details>

**8.2 ★ Is it a red-black tree?** For each tree, say whether it is a valid red-black tree. If not, name the violated property from Section 8.3. (B = black, R = red; missing children are black NIL leaves.)

```
(a)    B10          (b)    B10           (c)    B10          (d)    R10
      /   \               /   \                /   \               /   \
    R5    R15           B5    R15            B5    B15           B5    B15
             \               /   \                    \
             R20           B12   B20                  B20
```

<details>
<summary>Solution</summary>

(a) **Invalid, property 4.** R15 has a red child R20. Black counts are fine (every root-to-NIL path has one black node before NIL), so only the no-red-red rule fails.

(b) **Valid.** No red node has a red child, and every root-to-NIL path has exactly 2 black nodes before NIL: 10 and 5, or 10 and 12, or 10 and 20.

(c) **Invalid, property 5.** The path 10→15→NIL (15's empty left side) has 2 black nodes; the path 10→15→20→NIL has 3. Recoloring 20 red would fix it.

(d) **Invalid, property 2.** The root is red. Recoloring the root black is always safe: it adds one black node to every path equally. That is why `fix_violation` ends with `(*root)->color = BLACK`.

</details>

**8.3 ★★ Red-black insertion by hand.** Insert 10, 20, 30, 15, 13 into an empty red-black tree, using the three insertion cases of Section 8.3 (and their mirror images when the parent is a right child). For each insertion, say which cases fire and draw the tree.

<details>
<summary>Hint</summary>

New nodes are red. "Line" means the new node and its parent are on the same side (both left children or both right children); "triangle" means they are on opposite sides.

</details>

<details>
<summary>Solution</summary>

- **10**: becomes the root and is colored black. `B10`.
- **20**: red, right child of black 10. Parent is black, nothing to fix.
- **30**: red, right child of red 20. The uncle (10's left) is NIL, black. 30 and 20 are both right children: a line, so **Case 3 (mirror)**: color 20 black, 10 red, rotate left at 10.

  ```
        B20
       /   \
     R10   R30
  ```

- **15**: goes 20→10→right. Red parent R10, and the uncle R30 is red: **Case 1**. Color 10 and 30 black, 20 red, move z up to 20. 20 is the root, so the loop stops and the root is recolored black. The black-height of the tree just grew by one.

  ```
        B20
       /   \
     B10   B30
        \
        R15
  ```

- **13**: goes 20→10→15→left. Red parent R15, and the uncle (10's left) is NIL, black. 13 is a left child of 15, which is a right child of 10: a triangle, so **Case 2 (mirror)**: rotate right at 15, making 13 the parent of 15. Now z is 15 and its parent is 13, a line, so **Case 3 (mirror)**: color 13 black, 10 red, rotate left at 10.

  ```
          B20
         /   \
       B13   B30
       /  \
     R10  R15
  ```

Every root-to-NIL path has 2 black nodes, and no red node has a red child.

</details>

**8.4 ★★ The thinnest AVL trees.** Let N(h) be the minimum number of nodes in an AVL tree of height h (edges). (a) Show N(h) = N(h − 1) + N(h − 2) + 1 and compute N(0) through N(6). (b) What is the largest possible height of an AVL tree with 20 nodes? (c) Use N(h) = F(h + 3) − 1, where F is the Fibonacci sequence with F(1) = F(2) = 1, to derive the bound h ≤ 1.44 log₂(n + 1) from Section 8.2.

<details>
<summary>Hint</summary>

A minimum AVL tree of height h has a root, one subtree of height h − 1, and the other subtree as short as the balance rule allows.

</details>

<details>
<summary>Solution</summary>

(a) An AVL tree of height h needs one subtree of height h − 1. The other can be at most one shorter, so the smallest choice is height h − 2. Both subtrees must themselves be minimal, giving N(h) = N(h − 1) + N(h − 2) + 1, with N(0) = 1 (one node) and N(1) = 2 (root and one child).

| h | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| N(h) | 1 | 2 | 4 | 7 | 12 | 20 | 33 |

(b) N(5) = 20 and N(6) = 33 > 20, so a 20-node AVL tree can have height **5**, but not 6. A perfectly balanced 20-node tree has height 4, so the AVL tree is at most one level worse here.

(c) N(h) + 1 satisfies the Fibonacci recurrence: (N(h) + 1) = (N(h − 1) + 1) + (N(h − 2) + 1), with N(0) + 1 = 2 = F(3) and N(1) + 1 = 3 = F(4). So N(h) = F(h + 3) − 1. By induction, F(k) ≥ φ^(k − 2), where φ = (1 + √5)/2 ≈ 1.618 (it holds for k = 1, 2, and φ^(k−3) + φ^(k−4) = φ^(k−2) because φ² = φ + 1). An AVL tree with n nodes and height h therefore has

n ≥ N(h) = F(h + 3) − 1 ≥ φ^(h + 1) − 1

so h + 1 ≤ log_φ(n + 1) = log₂(n + 1) / log₂ φ ≈ 1.44 log₂(n + 1), and h < 1.44 log₂(n + 1). This is the source of the 1.44 constant, and also of the name "Fibonacci trees" for these worst-case AVL shapes.

</details>

**8.5 ★★ Splay a chain.** Insert 5, 4, 3, 2, 1 into a plain BST, giving a left-leaning chain with 5 at the root. (a) Splay node 1 to the root using the zig, zig-zig and zig-zag steps of Section 8.4, working from the bottom up. Draw the tree after each step and give the final height. (b) Then splay node 3 and draw the result.

<details>
<summary>Hint</summary>

Each step looks at x, its parent p and its grandparent g. Apply the rule, then repeat with x's new parent and grandparent. Use the subtree labels in the zig-zig diagram to see where each subtree goes.

</details>

<details>
<summary>Solution</summary>

(a) Start: 5→4→3→2→1, all left children; height 4.

**Step 1, zig-zig** (x = 1, p = 2, g = 3, both left children). By the diagram, x becomes the subtree root, p becomes x's right child, and g becomes p's right child. All T subtrees are empty. The result replaces 3 as the left child of 4:

```
        5
       /
      4
     /
    1
     \
      2
       \
        3
```

**Step 2, zig-zig** (x = 1, p = 4, g = 5, both left children). Here T2 (1's right subtree) is the chain 2→3, and it becomes 4's left subtree:

```
      1
       \
        4
       / \
      2   5
       \
        3
```

Final height **3**, down from 4. Node 1 went from depth 4 to the root, and the total depth of all nodes fell from 10 to 8. That roughly-halving of the access path is what pays for the amortized O(log n) bound; a plain move-to-root by single rotations would leave a chain of height 4 behind.

(b) 3 is the right child of 2, and 2 is the left child of 4: a **zig-zag** (x = 3, p = 2, g = 4). x moves up with p as its left child and g as its right child; 4 keeps 5 as its right child. 3 is now the right child of the root 1, so a final **zig** rotates 3 above 1:

```
        3
       / \
      1   4
       \   \
        2   5
```

Height **2**. Two accesses turned a height-4 chain into a nearly balanced tree.

</details>

**8.6 ★★ A treap's shape is determined by its keys and priorities.** Using the min-heap convention of `treap_insert` (smaller priority nearer the root), draw the treap holding these keys and priorities. Then prove that for distinct keys and distinct priorities, the treap is the same no matter what order the keys are inserted in.

| key | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| priority | 0.6 | 0.2 | 0.9 | 0.1 | 0.5 | 0.3 |

<details>
<summary>Hint</summary>

Which node must be the root? Once the root is fixed, which keys must go in its left subtree?

</details>

<details>
<summary>Solution</summary>

The root must hold the smallest priority, 0.1, so the root is **4**. By the BST property, keys {1, 2, 3} form its left subtree and {5, 6} its right. Apply the same rule to each side: on the left the smallest priority is 0.2, so 2 is that subtree's root, with 1 on its left and 3 on its right. On the right the smallest is 0.3, so 6 is the root of that side, and 5 is its left child.

```
          4 (0.1)
        /        \
    2 (0.2)      6 (0.3)
    /    \        /
 1 (0.6) 3 (0.9) 5 (0.5)
```

**Uniqueness, by induction on the number of keys.** With zero keys the treap is empty. Otherwise, the heap property forces the root to be the key with the minimum priority (priorities are distinct, so it is unique). The BST property then forces every smaller key into the left subtree and every larger key into the right. Each subtree is itself a treap on fewer keys, so by induction each is unique. Insertion order never enters the argument.

This is why random priorities give expected O(log n) height: the treap has exactly the shape of a plain BST built by inserting the keys in increasing priority order, and with random priorities that order is a uniformly random permutation. Section 7.3's average case then applies, whatever order the keys actually arrive in.

</details>

**8.7 ★★★ Prove the red-black height bound.** (a) Let bh(x) be the number of black nodes on any path from x down to a NIL leaf, counting the NIL but not x itself. Prove by induction that the subtree rooted at x contains at least 2^bh(x) − 1 internal (non-NIL) nodes, and conclude that a red-black tree with n nodes has height at most 2 log₂(n + 1). (b) Show that the factor of 2 can really occur by drawing a valid red-black tree whose longest root-to-NIL path has twice as many nodes as its shortest.

<details>
<summary>Hint</summary>

For (a), relate bh of a child to bh of its parent; the answer depends on the child's color. Then use property 4 to say what fraction of any root-to-leaf path must be black.

</details>

<details>
<summary>Solution</summary>

(a) **Claim:** subtree(x) has at least 2^bh(x) − 1 internal nodes. Induct on the height of x.

- *Base:* x is NIL. bh(x) = 0 and the subtree has 0 ≥ 2⁰ − 1 = 0 internal nodes.
- *Step:* x is internal with children c₁ and c₂. A black child has bh(c) = bh(x) − 1 and a red child has bh(c) = bh(x), so bh(c) ≥ bh(x) − 1 either way (property 5 makes bh well defined). Each child has smaller height, so by induction the subtree of x has at least

  (2^(bh(x)−1) − 1) + (2^(bh(x)−1) − 1) + 1 = 2^bh(x) − 1

  internal nodes.

Now let the tree have height h. Take a longest path from the root down to a NIL. Below the root it has h + 1 nodes (h internal nodes, then the NIL). Property 4 says no two reds are adjacent, and the NIL is black, so at least half of them are black: bh(root) ≥ (h + 1)/2 ≥ h/2. Applying the claim to the root:

n ≥ 2^(h/2) − 1, so h/2 ≤ log₂(n + 1), so **h ≤ 2 log₂(n + 1)**.

This is the argument behind the one-line summary in "Why Properties Guarantee Balance". Note the direction: the black-height is at *most* log₂(n + 1), which caps the height.

(b) Root B10 with a short left side and a long right side:

```
        B10
       /   \
     B5    R20
          /   \
        B15   B30
                 \
                 R40
```

Check: every root-to-NIL path has 2 black nodes before the NIL (10 and 5, 10 and 15, or 10 and 30), and red nodes 20 and 40 have only black children (including NIL). The shortest root-to-NIL path is 10→5 (2 nodes); the longest is 10→20→30→40 (4 nodes). The longest path alternates black and red and the shortest is all black, which is exactly the extreme that property 4 allows.

</details>

---

## Where this connects

- [Chapter 7: Binary Search Trees](ch07-binary-search-trees.md). The unbalanced baseline these structures fix
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). Why skip lists trade rotations for randomness
