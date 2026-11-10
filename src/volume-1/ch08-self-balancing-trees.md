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

Why is one rotation (single or double) enough for an insertion? Let z be the lowest unbalanced ancestor of the new node. Before the insertion z's subtree had some height H. The insertion pushed it to H + 1, and that extra level is what unbalanced z. The rotation at z removes exactly that level, so z's subtree is back to height H, the height it had before the insertion. Every ancestor above z sees the same subtree height as before, so nothing above z can be unbalanced.

### AVL Deletion

Deletion starts as BST deletion (Section 7.2): a node with two children takes its successor's key, and the successor, which has at most one child, is unlinked instead. Then, as with insertion, walk back up the search path, updating heights and rotating wherever a balance factor reaches ±2. Two things are different.

**The case is chosen from the child's balance factor, not the key.** The insertion code compares the new key with the child's key to tell Left-Left from Left-Right. A deletion removes a key from the *shorter* side, so the key says nothing about the shape of the taller side. Look at the taller child y instead. If y leans the same way as z, or not at all (balance factor 0), do a single rotation; if y leans the other way, do a double rotation. The balance-0 case never arises after an insertion (the child that just grew always leans one way), but it does after a deletion, and there a double rotation would leave a node unbalanced (Exercise 8.8).

**One rotation may not finish the job.** Say z is left-heavy and lost a level on the right. Before the deletion z had height H, with a left subtree of height H − 1 and a right subtree of height H − 2. After it the right subtree has height H − 3. A single rotation when y leans left, or a double rotation when y leans right, leaves the subtree with height H − 1: one *less* than before the deletion. So z's parent now sees a shorter child and may itself be unbalanced, and so may every ancestor above it. Only when y has balance 0 does the single rotation keep height H, and then the walk can stop.

Here is the AVL code in Python, with the four cases folded into one `rebalance` that insertion and deletion share. Heights follow the C code: an empty tree has height 0 and a leaf has height 1.

```python
class Node:
    def __init__(self, key):
        self.key = key
        self.left = self.right = None
        self.height = 1


def height(node):
    return node.height if node else 0


def get_balance(node):
    return height(node.left) - height(node.right)


def update(node):
    node.height = 1 + max(height(node.left), height(node.right))


def rotate_right(z):
    y = z.left
    z.left, y.right = y.right, z
    update(z)
    update(y)
    return y


def rotate_left(z):
    y = z.right
    z.right, y.left = y.left, z
    update(z)
    update(y)
    return y


def rebalance(node):
    update(node)
    balance = get_balance(node)
    if balance > 1:                          # left-heavy
        if get_balance(node.left) < 0:       # Left-Right: straighten first
            node.left = rotate_left(node.left)
        return rotate_right(node)            # Left-Left, or child balance 0
    if balance < -1:                         # right-heavy, the mirror image
        if get_balance(node.right) > 0:      # Right-Left
            node.right = rotate_right(node.right)
        return rotate_left(node)             # Right-Right, or child balance 0
    return node


def insert_avl(node, key):
    if node is None:
        return Node(key)
    if key < node.key:
        node.left = insert_avl(node.left, key)
    elif key > node.key:
        node.right = insert_avl(node.right, key)
    else:
        return node                          # duplicate
    return rebalance(node)


def delete_avl(node, key):
    if node is None:
        return None                          # key not present
    if key < node.key:
        node.left = delete_avl(node.left, key)
    elif key > node.key:
        node.right = delete_avl(node.right, key)
    else:
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left
        successor = min_value(node.right)    # Section 7.2
        node.key = successor.key
        node.right = delete_avl(node.right, successor.key)
    return rebalance(node)
```

`delete_avl` calls `rebalance` at every node on the way back up, so it handles the cascade without any special code. For simplicity it keeps rebalancing after the height stops changing; those extra calls find nothing to do.

**Worked example: a deletion that rotates twice.** The tree below is a *Fibonacci tree*, the thinnest AVL tree of its height (Exercise 8.4; heights here count nodes, as in the code, so they are one more than in that exercise). Every internal node is left-heavy, with balance factor +1. Delete 12.

```
Before (height 5):                    After deleting 12 (height 4):

              8                                   5
           /     \                             /     \
          5       11                          3       8
        /   \    /  \                        / \     /  \
       3     7  10   12                     2   4   7    10
      / \   /   /                          /       /    /  \
     2   4 6   9                          1       6    9    11
    /
   1
```

```
delete_avl(12)       12 is a leaf: return None, so 11.right = None
rebalance(11)        heights: left (10) = 2, right = 0, balance +2
                     child 10 has balance +1: Left-Left, rotate_right(11)
                     the subtree is now 10 with children 9 and 11, height 2 (was 3)
rebalance(8)         heights: left (5) = 4, right (10) = 2, balance +2
                     child 5 has balance +1: Left-Left, rotate_right(8)
                     5 is the new root; tree height 4 (was 5)
```

Both ancestors of the deleted leaf needed a rotation, because each rotation made its subtree one shorter, which unbalanced the next node up. In bigger Fibonacci trees the cascade keeps going: deleting the right leaf of the 232-node Fibonacci tree of height 11 causes 5 rotations, about one for every two levels. An insertion into any AVL tree never needs more than 2.

**Cost.** Each level of the path does O(1) work: update a height and do at most one single or double rotation. Deletion is therefore O(log n) worst case, with O(log n) rotations in the worst case, against O(1) rotations for insertion.

**Testing it.** A balanced tree can return the right answers while silently breaking its invariant, so check the invariant, not just the answers. After every operation, compare the tree's in-order keys with a sorted Python list that receives the same operations, and verify every node's stored height and balance factor:

```python
import bisect
import random


def min_value(node):                         # Section 7.2
    while node.left:
        node = node.left
    return node


def check_avl(node, lo=None, hi=None):
    """Return the keys in order; fail if order, a height or a balance is wrong."""
    if node is None:
        return []
    assert (lo is None or lo < node.key) and (hi is None or node.key < hi)
    keys = check_avl(node.left, lo, node.key) + [node.key] \
        + check_avl(node.right, node.key, hi)
    assert node.height == 1 + max(height(node.left), height(node.right))
    assert abs(get_balance(node)) <= 1
    return keys


root, reference = None, []
for _ in range(5000):
    key = random.randrange(300)
    if random.random() < 0.5:
        root = insert_avl(root, key)
        if key not in reference:
            bisect.insort(reference, key)
    else:
        root = delete_avl(root, key)
        if key in reference:
            reference.remove(key)
    assert check_avl(root) == reference
```

The children are checked before the parent, so each stored height is compared against children whose heights have already been verified.

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

### Deletion and the Double Black

Deletion is where red-black trees earn their reputation. Start with BST deletion (Section 7.2): if the node has two children, copy in its successor's key and remove the successor instead. Either way, the node y that is physically unlinked has at most one child, x (possibly a NIL leaf), which takes y's place.

- **y was red.** No path lost a black node, and y's neighbours were black, so no red-red appears. Done.
- **y was black and x is red.** Color x black. The paths through x get their black node back. Done.
- **y was black and x is black** (usually x is NIL). Every path through x now has one black node too few, breaking property 5. Pretend x carries an *extra black*: it is **double black** and counts twice. The counts are now correct, and the rest of the algorithm moves the extra black around until it can be dropped.

Let x be a left child, p its parent and w its sibling (the cases for a right child are mirror images). w cannot be NIL: before the deletion, every path down x's side passed through the removed black node y, so every path down w's side contains a black node too, besides its final NIL.

| Case | Situation | Action | Then |
|------|-----------|--------|------|
| 1 | w is red | Rotate left at p; swap the colors of p and w | x has a black sibling: go to case 2, 3 or 4 |
| 2 | w is black, both its children black | Color w red; move the extra black up to p | p red: color it black, done. p black: p is double black, repeat one level up |
| 3 | w is black, near child (w.left) red, far child black | Rotate right at w; swap the colors of w and its old near child | Now the far child is red: case 4 |
| 4 | w is black, far child (w.right) red | Rotate left at p; w takes p's color; p and the far child become black | Done |

In case 2, coloring w red removes one black from every path on w's side, matching the shortage on x's side; the whole subtree at p is now one short, which is what moving the extra black up to p records. In case 4 the rotation puts p, now black, above x, giving x's paths the black node they were missing, while w (in p's old position and color) and the far child (now black) keep the counts on the other side. If the extra black reaches the root, drop it: every path loses one black node at once, which property 5 allows.

**Cost.** Case 2 can repeat up the tree, but it only recolors. A case 1 rotation is followed by case 2 with a red parent (which stops) or by case 3 or 4 (which stop), so a deletion makes **at most 3 rotations** (cases 1, 3, 4) and O(log n) recolorings: O(log n) worst case. AVL deletion may need a rotation on many levels; this bounded number of structural changes is one reason libraries prefer red-black trees for update-heavy maps.

**Worked example.** Insert 10, 20, ..., 100 in order, then delete 10:

```
Before:                                  After deleting 10:
              B40                                      B60
           /       \                                /       \
       B20           B60                        B40           B80
      /   \         /    \                     /   \         /   \
    B10   B30     B50     R80                B20   B50     B70   B90
                         /   \                  \                   \
                       B70   B90                R30                 R100
                                \
                                R100
```

```
remove 10          10 is a black leaf: its NIL is double black (x), p = 20, w = 30
case 2 at 20       w = 30 is black with black (NIL) children: color 30 red,
                   the extra black moves to 20, which is black, so continue
case 4 at 40       x = 20, p = 40, w = 60 is black, far child 80 is red:
                   rotate left at 40; 60 takes 40's color (black);
                   40 and 80 become black. Done
```

Every root-to-NIL path still has 3 black nodes before the NIL, and no red node has a red child. The recoloring and rotation look arbitrary here; Section 8.4 shows that they are a B-tree merge followed by a B-tree borrow.

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

## 8.4 Red-Black Trees Are 2-3-4 Trees

The five red-black properties and the case analyses above look like a list of tricks. They are a B-tree in disguise. A **2-3-4 tree** is a B-tree of order 4 ([Chapter 10](ch10-multiway-search-trees-and-b-trees.md)): every node holds 1, 2 or 3 keys and has 2, 3 or 4 children, and all leaves are at the same depth. Take any red-black tree and merge every red node into its parent. Each black node, together with its red children, becomes one 2-3-4 node:

| 2-3-4 node | Red-black encoding |
|------------|--------------------|
| 2-node `[b]` | a black node with no red children |
| 3-node `[a b]` | a black node with one red child (b black with red left child a, or a black with red right child b) |
| 4-node `[a b c]` | the middle key b, black, with red children a and c |

Run the merge backwards and any 2-3-4 tree becomes a red-black tree. The correspondence is not one-to-one, because a 3-node can lean either way.

<figure>
{{#include ../images/rb-234.svg}}
<figcaption>Each shaded group is one 2-3-4 node: a black node plus its red children. Inserting 80 recolors three nodes, and in the 2-3-4 tree that is a 4-node split that pushes 60 up into its parent.</figcaption>
</figure>

### What the Rules Mean

With the 2-3-4 tree in view, each red-black property states a B-tree fact:

- **No red node has a red child** keeps every group to one black node and at most two red children, so a node never holds more than 3 keys.
- **Every path has the same number of black nodes**: each 2-3-4 node contains exactly one black node, so a path's black count is the number of 2-3-4 levels it crosses. Equal black counts means all 2-3-4 leaves are at the same depth, which is the B-tree invariant and the whole source of the balance.
- **The root is black** because the top of every group is black.
- **The height bound** follows in one line. A 2-3-4 tree of n keys has at most log₂(n + 1) levels, since every node has at least 2 children, and each level becomes at most two red-black levels (a black node and a red child). So the red-black height is at most 2 log₂(n + 1), the bound of Section 8.3.

### Insertion Is Splitting

A new red-black node is red, which means a new key joins an existing 2-3-4 leaf. That matches B-tree insertion, which always adds to a leaf.

- **Parent is black.** The leaf was a 2-node or a 3-node, and the key fits: a 2-node becomes a 3-node, and a 3-node becomes a 4-node already in the standard shape (black middle, two red children). Done.
- **Case 1, red uncle.** The parent and the uncle are both red children of the grandparent, so the grandparent's group is a 4-node, and the new key would be its fourth. The B-tree answer is to split: the middle key moves up into the parent node and the two halves become separate nodes. Recoloring does exactly that. The grandparent turns red, which moves it up into its own parent's group; the parent and uncle turn black, so they become the tops of two separate nodes. If the grandparent's parent is also red, the node above has overflowed in turn: continue from there, as a B-tree split propagates upward. When the split reaches the root, recoloring the root black creates a new top level, the only way either tree grows taller.
- **Cases 2 and 3, black uncle.** The grandparent's group is a 3-node (the black uncle belongs to a different node), so there is room for the new key, and the result is a 4-node. But its three keys form a chain of two red links instead of a black middle key with two red children. The rotations reshape the chain into that standard form. The 2-3-4 tree does not change; only its encoding does.

The figure shows Case 1. Inserting 80 under red 70 meets the 4-node `[50 60 70]`. Coloring 50 and 70 black and 60 red splits it: 60 joins the root, which becomes the 4-node `[20 40 60]`, and 80 joins 70 to form the 3-node `[70 80]`. The parent of 60 is black, so the process stops there with no rotation at all.

### Deletion Is Borrowing and Merging

Deletion maps onto Chapter 10's B-tree deletion in the same way. Removing a red node, or a black node with a red child, takes a key out of a 3-node or 4-node, which still has a key left. A double black is an **underflow**: a 2-node has lost its only key. The four cases are the B-tree repairs:

- **Case 2 (black sibling, both children black)**: the sibling is a 2-node, so there is nothing to borrow. **Merge**: the parent key comes down and joins the sibling, and coloring w red puts the two in one group. If p was red, the parent node had keys to spare; coloring p black finishes the merge. If p was black, the parent was itself a 2-node and is now empty: the underflow moves up a level, just as a B-tree merge can propagate to the root. When it reaches the root, the tree loses a level.
- **Cases 3 and 4 (black sibling with a red child)**: the sibling is a 3-node or 4-node. **Borrow** through the parent: the parent key comes down into the empty node and a sibling key goes up to replace it (from a 4-node sibling, the key nearest x comes across as well). Case 4's rotation does this in one step; case 3 only reshapes the sibling so that case 4's rotation applies.
- **Case 1 (red sibling)**: w is red, so it is in the same group as p. The parent's 2-3-4 node is a 3-node encoded with the wrong lean, and x's red-black sibling is not its 2-3-4 sibling. The rotation flips the lean, and nothing in the 2-3-4 tree changes. After it, x's sibling is a real 2-3-4 sibling, and case 2, 3 or 4 applies.

Here is the worked deletion of Section 8.3 again, as a 2-3-4 tree:

```
Before:                    [40]
                     /             \
                 [20]               [60 80]
                /    \            /    |    \
             [10]   [30]       [50]  [70]  [90 100]

Delete 10: [10] is empty. Its sibling [30] is a 2-node, so merge:
20 comes down and joins 30, giving [20 30]. Now [20]'s old node is empty
(case 2 with a black parent). Its sibling [60 80] is a 3-node, so borrow:
40 comes down, 60 goes up (case 4).

After:                     [60]
                     /             \
                 [40]               [80]
                /    \             /    \
           [20 30]  [50]        [70]  [90 100]
```

Read the "after" tree of Section 8.3 back through the table above and you get exactly this.

This view explains why the classic algorithm has so many cases. A 2-3-4 tree has one operation for each situation (add a key, split, merge, borrow), but the binary encoding has several shapes for each 3-node and 4-node in transit, and each shape has its own case and its own mirror image. Rudolf Bayer introduced the structure in 1972 as the *symmetric binary B-tree*, a binary representation of B-trees with "horizontal" links where red links are now; the red and black colors came later. The next section shows what happens when the encoding is restricted to one shape per node.

## 8.5 Left-Leaning Red-Black Trees

Robert Sedgewick's **left-leaning red-black tree** (LLRB, 2008) removes the choice. It adds one rule: a red node must be a left child. Thinking of a red node as a red *link* from its parent, the invariant is:

1. Red links lean left.
2. No node has two red links touching it.
3. Every path from the root to a NIL link has the same number of black links.

Rule 2 forbids a red node with a red child and also a black node with two red children, so there are no 4-nodes. An LLRB tree is a 2-3 tree in which each 3-node is drawn one way, black on top with a red left child. Each 2-3 tree has exactly one LLRB encoding, so the mirror-image cases disappear.

### Insertion

A new key is attached with a red link, as before. Then, on the way back up the recursion, three local fixes repair whatever the insertion broke, in this order:

```python
RED, BLACK = True, False


class LLRBNode:
    def __init__(self, key):
        self.key = key
        self.left = self.right = None
        self.color = RED                     # a new key joins an existing node


def is_red(h):
    return h is not None and h.color == RED


def rotate_left(h):                          # a red right link now leans left
    x = h.right
    h.right, x.left = x.left, h
    x.color, h.color = h.color, RED
    return x


def rotate_right(h):                         # a red left link now leans right
    x = h.left
    h.left, x.right = x.right, h
    x.color, h.color = h.color, RED
    return x


def flip_colors(h):                          # split a temporary 4-node
    h.color = not h.color
    h.left.color = not h.left.color
    h.right.color = not h.right.color


def fix_up(h):
    if is_red(h.right) and not is_red(h.left):
        h = rotate_left(h)                   # right-leaning 3-node
    if is_red(h.left) and is_red(h.left.left):
        h = rotate_right(h)                  # 4-node as a chain of two reds
    if is_red(h.left) and is_red(h.right):
        flip_colors(h)                       # balanced 4-node: split it
    return h


def llrb_insert(root, key):
    root = _insert(root, key)
    root.color = BLACK
    return root


def _insert(h, key):
    if h is None:
        return LLRBNode(key)
    if key < h.key:
        h.left = _insert(h.left, key)
    elif key > h.key:
        h.right = _insert(h.right, key)
    return fix_up(h)
```

(These `rotate_left` and `rotate_right` belong with `LLRBNode`, not with the AVL code of Section 8.2: they move colors, not heights.)

Each line of `fix_up` is one 2-3 tree situation. A red right link with a black left link is a 3-node leaning the wrong way: rotate it left. Two red links in a row on the left are a 4-node drawn as a chain: rotate right to balance it. Two red children are a balanced 4-node: flip the colors, which splits it and passes the middle key up as a red link to the parent, where the next `fix_up` call deals with it. The three classic insertion cases and their mirror images all reduce to these three lines, applied at every node on the search path.

Insertion is O(log n) worst case. Sedgewick's paper also gives a variant that calls `flip_colors` on the way *down*, before the recursive calls; it splits 4-nodes top-down and keeps them, so it is the 2-3-4 version. The code above, with the flip last, is the 2-3 version used in Sedgewick and Wayne's *Algorithms* (4th edition).

### Deletion

Deletion uses the same plan as Chapter 10's single-pass B-tree deletion: never step down into a node that has only one key, so that the key to be removed is never the only key in its leaf. `move_red_left` makes sure the left child is not a 2-node before the descent goes left. It first flips colors, merging the parent key and both children into a temporary 4-node; if the right sibling was a 3-node, it then borrows from it instead, with two rotations and a flip back. On the way back up, `fix_up` cleans up the temporary 4-nodes and right-leaning links left behind.

```python
def move_red_left(h):
    # h is red and h.left is a 2-node: give h.left a red link
    flip_colors(h)                           # merge h.left, h, h.right
    if is_red(h.right.left):                 # sibling is a 3-node: borrow
        h.right = rotate_right(h.right)
        h = rotate_left(h)
        flip_colors(h)
    return h


def move_red_right(h):
    flip_colors(h)
    if is_red(h.left.left):
        h = rotate_right(h)
        flip_colors(h)
    return h


def delete_min(h):
    if h.left is None:
        return None
    if not is_red(h.left) and not is_red(h.left.left):
        h = move_red_left(h)
    h.left = delete_min(h.left)
    return fix_up(h)


def llrb_delete(root, key):                  # key must be in the tree
    if not is_red(root.left) and not is_red(root.right):
        root.color = RED
    root = _delete(root, key)
    if root is not None:
        root.color = BLACK
    return root


def _delete(h, key):
    if key < h.key:
        if not is_red(h.left) and not is_red(h.left.left):
            h = move_red_left(h)
        h.left = _delete(h.left, key)
    else:
        if is_red(h.left):
            h = rotate_right(h)              # lean right so a red link goes down
        if key == h.key and h.right is None:
            return None                      # h is a red leaf: drop it
        if not is_red(h.right) and not is_red(h.right.left):
            h = move_red_right(h)
        if key == h.key:
            successor = h.right
            while successor.left:
                successor = successor.left
            h.key = successor.key
            h.right = delete_min(h.right)
        else:
            h.right = _delete(h.right, key)
    return fix_up(h)
```

The precondition matters: with an absent key, the descent can reach `h.left.left` on a missing child. Check membership first (an O(log n) search) when the caller cannot guarantee it. Both operations are O(log n) worst case.

The same kind of test as for the AVL tree checks every LLRB rule after every operation:

```python
import bisect
import random


def check_llrb(h, lo=None, hi=None):
    """Return (black height, keys in order); fail if any LLRB rule is broken."""
    if h is None:
        return 0, []
    assert (lo is None or lo < h.key) and (hi is None or h.key < hi)
    assert not is_red(h.right)                     # red links lean left
    assert not (is_red(h) and is_red(h.left))      # never two reds in a row
    black_left, left = check_llrb(h.left, lo, h.key)
    black_right, right = check_llrb(h.right, h.key, hi)
    assert black_left == black_right               # perfect black balance
    return black_left + (not is_red(h)), left + [h.key] + right


root, reference = None, []
for _ in range(5000):
    key = random.randrange(300)
    if random.random() < 0.5:
        root = llrb_insert(root, key)
        if key not in reference:
            bisect.insort(reference, key)
    elif key in reference:
        root = llrb_delete(root, key)
        reference.remove(key)
    assert not is_red(root)
    assert check_llrb(root)[1] == reference
```

### Trade-offs

The LLRB insertion is short enough to write from memory, and that is its real contribution: it makes the 2-3 correspondence visible in code. But it is not a better red-black tree in every respect.

- **Deletion is still fiddly.** The deletion code is more than twice the length of the insertion code, and it is harder to check by eye, because it deliberately creates temporary right-leaning links and 4-nodes and relies on `fix_up` to remove them later.
- **More rotations.** A classic insertion makes at most 2 rotations. The LLRB insertion keeps rotating on the way up to restore the left lean, sometimes at many levels. Inserting 100,000 random keys with the code above averaged about 1.19 rotations per insertion, with up to 13 in a single insertion; the classic algorithm averaged about 0.58 on the same keys.
- **Recursion without parent pointers.** That makes the code short, but production trees usually keep parent pointers anyway, for iterators and for deleting a node the caller already holds, and then the classic bottom-up fix-up is just as natural. Java's `TreeMap` (adapted from Cormen, Leiserson and Rivest), libstdc++'s `std::map` and the Linux kernel's `rbtree` all use the classic algorithm.

Arne Andersson's AA tree (1993, Chapter 7) made the mirror-image choice earlier, requiring red links to lean right; its two fix-up steps, *skew* and *split*, play the role of `fix_up`'s three lines.

## 8.6 Splay Trees

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

## 8.7 Scapegoat Trees

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

## 8.8 Treaps

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

## 8.9 Performance Comparison

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

## 8.10 Real-World Usage

| Tree Type | Real-World Uses |
|-----------|----------------|
| Red-Black | Linux kernel (completely fair scheduler), Java's TreeMap/TreeSet, C++ STL (typically) |
| AVL | Databases with frequent lookups, file systems |
| Splay | Network routing (LRU caches), memory allocators |
| Treap | Skip list alternative in some databases |

## 8.11 Historical Context

Georgy Adelson-Velsky and Evgenii Landis described the AVL tree in 1962 ("An algorithm for the organization of information", *Doklady Akademii Nauk SSSR*), the first binary search tree with a worst-case O(log n) height guarantee.

Rudolf Bayer, co-inventor of the B-tree (Chapter 10), introduced *symmetric binary B-trees* in 1972 (*Acta Informatica*): B-trees of order 4 stored as binary nodes, the structure of Section 8.4. Leonidas Guibas and Robert Sedgewick recast them in 1978 with the red and black coloring ("A dichromatic framework for balanced trees", FOCS), and used the coloring as a common framework for many balanced-tree schemes. The double-black formulation of deletion in Section 8.3 follows Cormen, Leiserson and Rivest's *Introduction to Algorithms* (1990). Sedgewick returned to the structure thirty years later with the left-leaning variant of Section 8.5 (2008).

Daniel Sleator and Robert Tarjan introduced splay trees in "Self-adjusting binary search trees" (*Journal of the ACM*, 1985). Scapegoat trees are named in Igal Galperin and Ronald Rivest's 1993 paper (SODA); Arne Andersson had described essentially the same partial-rebuilding scheme in 1989. Treaps come from Cecilia Aragon and Raimund Seidel's "Randomized search trees" (FOCS 1989; journal version by Seidel and Aragon in *Algorithmica*, 1996). The shape they rely on, a tree that is a BST on keys and a heap on a second value, is Jean Vuillemin's *Cartesian tree* (1980).

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

**8.5 ★★ Splay a chain.** Insert 5, 4, 3, 2, 1 into a plain BST, giving a left-leaning chain with 5 at the root. (a) Splay node 1 to the root using the zig, zig-zig and zig-zag steps of Section 8.6, working from the bottom up. Draw the tree after each step and give the final height. (b) Then splay node 3 and draw the result.

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

**8.8 ★★ Why deletion looks at the child's balance factor.** The AVL tree below is what `insert_avl` builds from 20, 10, 60, 5, 40, 80, 30, 70. (a) Delete 5 with `delete_avl`. Which node becomes unbalanced, which rotation is done, and does the walk up need to continue? (b) The C `insert_avl` picks the case by comparing the key with the child's key. Since 5 < 60, that test would choose Right-Left. Do that double rotation instead and show that the result is not an AVL tree.

```
        20
       /  \
     10    60
     /    /  \
    5    40   80
        /    /
       30   70
```

<details>
<summary>Hint</summary>

Compute the balance factor of 60 before deciding anything. It is the case that never happens after an insertion.

</details>

<details>
<summary>Solution</summary>

(a) Removing the leaf 5 leaves 10 as a leaf (height 1). At 20 the left height is 1 and the right height (60) is 3, so the balance factor is −2. The taller child 60 has balance 0: its subtrees 40 and 80 both have height 2. `rebalance` sees `get_balance(node.right) > 0` is false and does a single `rotate_left(20)`:

```
          60
        /    \
      20      80
     /  \     /
   10    40  70
        /
      30
```

20 has balance 1 − 2 = −1 and 60 has balance 3 − 2 = +1, so the tree is valid. Its height is 4, the same as before the deletion, so no ancestor could be affected and the walk could stop here. (This is the one case where a deletion's rotation does not shorten the subtree.)

(b) The double rotation first does `rotate_right(60)`, lifting 40, then `rotate_left(20)`:

```
          40
        /    \
      20      60
     /  \       \
   10    30      80
                /
              70
```

Node 60 has an empty left subtree and a right subtree of height 2: balance −2. The double rotation is right only when the inner grandchild (40) is the taller part of 60's subtree. When 60 is balanced, moving 40 up leaves 80's whole subtree hanging under 60 with nothing on the other side. Insertion never meets this case because the child that just grew always leans one way, which is why the C code can get away with comparing keys.

</details>

**8.9 ★★ Red-black deletion, two views.** Start again from the red-black tree that inserting 10, 20, ..., 100 produces (the "before" tree of the worked deletion in Section 8.3) and delete 40, the root. (a) Trace the deletion: which node is physically removed, and which cases of the double-black table fire? Draw the result. (b) Redo it on the corresponding 2-3-4 tree (Section 8.4) and check that the two results correspond.

<details>
<summary>Hint</summary>

40 has two children, so its successor is removed instead. Look at the color of the double black's sibling first.

</details>

<details>
<summary>Solution</summary>

(a) The successor of 40 is 50, the minimum of the right subtree. 50's key is copied into the root, and the node that held 50, a black leaf, is unlinked. Its NIL is double black, with parent p = 60 and sibling w = 80.

- **Case 1**: w = 80 is red. Rotate left at 60 and swap the colors of 60 and 80: 80 is now black, with red left child 60. x's new sibling is 70, black.
- **Case 2**: 70 is black with two black (NIL) children. Color 70 red and move the extra black to p = 60. 60 is red, so color it black. Done.

```
              B50
           /       \
       B20           B80
      /   \         /    \
    B10   B30     B60     B90
                     \       \
                     R70     R100
```

Every root-to-NIL path still has 3 black nodes, and no red node has a red child. The repair took one rotation and four color changes.

(b) The 2-3-4 tree is `[40]` at the root, with children `[20]` (over `[10]` and `[30]`) and `[60 80]` (over `[50]`, `[70]` and `[90 100]`). Deleting 40 from an internal node replaces it with its successor 50 from a leaf, which leaves the leaf `[50]` empty. Its 2-3-4 sibling is `[70]`, a 2-node, so **merge**: the separating key 60 comes down and joins 70, giving `[60 70]`, and the parent `[60 80]` shrinks to `[80]`. The parent still has a key, so the repair stops.

```
                 [50]
           /             \
       [20]               [80]
      /    \             /     \
   [10]   [30]      [60 70]   [90 100]
```

Reading the red-black result as groups gives exactly this. Case 1 did not change the 2-3-4 tree: the 3-node `[60 80]` was encoded with 60 on top, which made 80 the red-black sibling of the empty node even though its real 2-3-4 sibling was `[70]`. The rotation re-encoded the same 3-node with 80 on top. Case 2 with a red parent is a merge that the parent can absorb.

</details>

**8.10 ★★ LLRB insertion by hand.** Insert 1, 2, 3, 4, 5, 6, 7 in that order into an empty LLRB tree with `llrb_insert` (Section 8.5). After each insertion, say which of the three lines of `fix_up` fire (and at which node), draw the tree, and give the 2-3 tree it encodes.

<details>
<summary>Solution</summary>

Red nodes are marked R; everything else is black.

| Insert | `fix_up` actions | LLRB tree | 2-3 tree |
|--------|------------------|-----------|----------|
| 1 | none | 1 | `[1]` |
| 2 | rotate left at 1 (red right link) | 2 with left child R1 | `[1 2]` |
| 3 | flip at 2 (two red children); the root is then reset to black | 2 with children 1 and 3 | `[2]` over `[1]`, `[3]` |
| 4 | rotate left at 3 | 2 with children 1 and 4; 4 has left child R3 | `[2]` over `[1]`, `[3 4]` |
| 5 | flip at 4, which makes 4 red, a red right link of 2; then rotate left at 2 | 4 with children R2 and 5; 2 has children 1 and 3 | `[2 4]` over `[1]`, `[3]`, `[5]` |
| 6 | rotate left at 5 | as before, but 6 replaces 5, with left child R5 | `[2 4]` over `[1]`, `[3]`, `[5 6]` |
| 7 | flip at 6, then flip at 4 (2 and 6 are both red); the root is reset to black | perfect tree: 4; 2, 6; 1, 3, 5, 7; all black | `[4]` over `[2]`, `[6]`, over `[1]`, `[3]`, `[5]`, `[7]` |

```
After 5:            After 7:
      B4                  B4
     /  \               /    \
   R2    B5           B2      B6
  /  \               /  \    /  \
B1    B3           B1   B3  B5   B7
```

Insertion 5 shows a split propagating: the flip at 4 splits the temporary 4-node `[3 4 5]` and sends 4 up as a red right link, and the rotation at 2 makes `[2 4]` a left-leaning 3-node. Insertion 7 splits two 4-nodes in a row, `[5 6 7]` and then `[2 4 6]`, and the second split happens at the root, so the tree gains a level. Sorted input, the worst case for a plain BST, gives a perfectly balanced tree here, and that continues: inserting 1 to 2^k − 1 in order gives a perfect all-black tree (checked with the code above for every k up to 12).

</details>

---

## Where this connects

- [Chapter 7: Binary Search Trees](ch07-binary-search-trees.md). The unbalanced baseline these structures fix
- [Chapter 10: Multiway Search Trees and B-Trees](ch10-multiway-search-trees-and-b-trees.md). The 2-3-4 trees and B-tree splits, borrows and merges that red-black trees encode (Section 8.4)
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). Why skip lists trade rotations for randomness
