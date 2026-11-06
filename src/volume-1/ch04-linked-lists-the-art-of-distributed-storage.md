# Chapter 4: Linked Lists—The Art of Distributed Storage

## 4.1 The Linked List Philosophy

Where arrays store elements contiguously, linked lists store elements anywhere in memory, connecting them via pointers. This distribution enables efficient insertion and deletion at arbitrary positions, at the cost of no direct indexing.

The fundamental trade-off:
- Array: Fast access, slow modification
- Linked list: Slow access (must traverse), fast modification

## 4.2 Singly Linked Lists

Each node contains data and a pointer to the next node:

```c
struct Node {
    element_type data;
    struct Node *next;
};
```

```
HEAD                                                            NULL
 │                                                               │
 ▼                                                               ▼
┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐
│ Data: A│ Next: ──────→│ Data: B│ Next: ──────→│ Data: C│ Next: ──────→│ Data: D│ Next: │
│       │       │    │       │       │    │       │       │    │       │       │
└────────┴───────┘    └────────┴───────┘    └────────┴───────┘    └────────┴───────┘
```

### Core Operations

**Insertion at Head:**
```c
void insert_head(Node **head_ref, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = *head_ref;
    *head_ref = new_node;
}
```
Time: O(1)

**Insertion at Position:**
```c
void insert_after(Node *prev_node, element_type data) {
    if (prev_node == NULL) return;
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = prev_node->next;
    prev_node->next = new_node;
}
```
Time: O(1) given position, O(n) to find position

**Deletion:**
```c
void delete_node(Node **head_ref, element_type key) {
    Node *temp = *head_ref;
    Node *prev = NULL;

    if (temp != NULL && temp->data == key) {
        *head_ref = temp->next;
        free(temp);
        return;
    }

    while (temp != NULL && temp->data != key) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL) return;
    prev->next = temp->next;
    free(temp);
}
```
Time: O(n) worst case to find, O(1) to delete

**Search:**
```c
Node* search(Node *head, element_type key) {
    Node *current = head;
    while (current != NULL) {
        if (current->data == key) return current;
        current = current->next;
    }
    return NULL;
}
```
Time: O(n)

## 4.3 Doubly Linked Lists

Each node contains data, a pointer to the next node, and a pointer to the previous node:

```c
struct DNode {
    element_type data;
    struct DNode *next;
    struct DNode *prev;
};
```

```
 NULL                                                           NULL
  │                                                             │
  │     ┌────────┬────────┬───────┐    ┌────────┬────────┬───────┐
  │     │  Prev  │  Data  │  Next │    │  Prev  │  Data  │  Next │
  └────→│  NULL  │   A    │   ────┼───→│   ────┤   B    │   ────┼───→ NULL
        └────────┴────────┴───────┘    └────────┴────────┴───────┘
```

### Advantages Over Singly Linked Lists

- Traversal in both directions
- O(1) deletion given a node pointer (no need to find previous)
- O(1) insertion before a given node
- Better for implementing deques

### Implementation

**Deletion (given node pointer):**
```cpp
void delete_node(DNode *node) {
    if (node->prev != NULL)
        node->prev->next = node->next;
    else
        head = node->next;  // Was head

    if (node->next != NULL)
        node->next->prev = node->prev;

    free(node);
}
```

**Insertion Before:**
```cpp
void insert_before(DNode **head, DNode *next_node, element_type data) {
    DNode *new_node = malloc(sizeof(DNode));
    new_node->data = data;
    new_node->next = next_node;
    new_node->prev = next_node->prev;

    if (next_node->prev != NULL)
        next_node->prev->next = new_node;
    else
        *head = new_node;  // Was head

    next_node->prev = new_node;
}
```

## 4.4 Circular Linked Lists

The last node's next pointer points back to the first node (or for doubly, the first node's prev points to the last).

```
Circular Singly:
┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐
│ Data: A│ Next: ────┼─→│ Data: B│ Next: ────┼─→│ Data: C│ Next: ────┐
│       │       │    │       │       │    │       │       │    │
└────────┴───────┘    └────────┴───────┘    └────────┴───────┘    │
    ↑                                                              │
    └──────────────────────────────────────────────────────────────┘

Circular Doubly:
NULL ◄────────────────────────────────────────────────────────────────► NULL
  │     ┌────────┬────────┬───────┐    ┌────────┬────────┬───────┐    │
  │     │  Prev  │  Data  │  Next │    │  Prev  │  Data  │  Next │    │
  └────→│   ●    │   A    │   ────┼───→│   ────┤   B    │   ────┼───→│
        └────────┴────────┴───────┘    └────────┴────────┴───────┘    │
            ▲                                                              │
            └──────────────────────────────────────────────────────────────┘
```

### Applications

**Round-Robin Scheduling**: Each process gets equal CPU time
**Circular Buffers**: Efficient producer-consumer patterns
**Music Playlists**: Seamless looping
**Undo/Redo History**: Recent actions cycle through

## 4.5 The Sentinel's Guard

Sentinel nodes (dummy nodes) simplify boundary conditions by eliminating null checks:

```c
// Without sentinel - careful null handling
void insert_first(Node **head, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = *head;
    *head = new_node;
}

// With sentinel - cleaner code
void insert_after(Node *prev, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = prev->next;
    prev->next = new_node;
}
```

Common sentinel patterns:
- **Head sentinel**: Dummy node before first real element
- **Tail sentinel**: Dummy node after last real element
- **Both**: Simplifies all operations to "insert after/before"

## 4.6 XOR Linked Lists

XOR linked lists store only the XOR of consecutive node addresses, saving space:

```c
struct XorNode {
    element_type data;
    uintptr_t npx;  // XOR of previous and next pointers
};
```

The trick: to traverse, you need the previous node's address to XOR with npx to get the next node's address.

**Traversal:**
```c
XorNode* prev = NULL;
XorNode* current = head;
XorNode* next;

while (current != NULL) {
    printf("%d ", current->data);
    next = (XorNode*)((uintptr_t)prev ^ current->npx);
    prev = current;
    current = next;
}
```

**Advantages**: 50% space reduction for pointers
**Disadvantages**: Can't traverse backwards without storing previous pointer, debugging is harder

## 4.7 Unrolled Linked Lists

Each node contains multiple elements in a small array:

```
┌────────┬───────┐    ┌────────┬───────┐
│ 3 │ A │ B │ C │ ──┼─→│ 2 │ D │ E │ ──┼─→ NULL
│ elements│       │    │ elements│       │
└────────┴───────┘    └────────┴───────┘
```

**Advantages:**
- Better cache locality (multiple elements per node)
- Less pointer overhead
- Faster iteration
- Still O(1) insertion at arbitrary positions (with smaller shift)

**Used in**: CD-ROM filesystems (directory entries), Kyoto Cabinet database, Lua's table implementation

## 4.8 Performance Characteristics

| Operation | Singly | Doubly | Circular | Unrolled |
|-----------|--------|--------|----------|----------|
| Insert at Head | O(1) | O(1) | O(1) | O(1)* |
| Insert at Tail | O(1)* | O(1) | O(1) | O(1)* |
| Delete at Head | O(1) | O(1) | O(1) | O(1)* |
| Delete at Tail | O(n) | O(1) | O(1)* | O(1)* |
| Delete at Position | O(n) | O(n)* | O(n) | O(n)* |
| Search | O(n) | O(n) | O(n) | O(n) |
| Memory Overhead | Low | Medium | Low | Low-Medium |
| Cache Efficiency | Poor | Poor | Poor | Better |

*With tail pointer or other augmentation

## 4.9 When to Use Linked Lists

**Use Linked Lists When:**
- Frequent insertions/deletions at arbitrary positions
- Size is unknown or highly variable
- Memory is fragmented
- No random access needed
- Implementing other structures (stacks, queues)

**Avoid Linked Lists When:**
- Frequent random access (use arrays)
- Cache performance matters (use arrays or unrolled)
- Memory overhead is a concern (pointers take space)
- Simple iteration is the primary operation (vectors are faster)

## 4.10 Real-World Applications

**Operating Systems**:
- Process scheduling queues
- Memory allocation (free lists)
- File system directory entries
- Driver device queues

**Databases**:
- B-tree leaf nodes (doubly linked for range scans)
- Transaction logs
- Lock chains

**Compilers**:
- Symbol tables (hash table + linked list chaining)
- Abstract syntax trees (child lists)

**Applications**:
- Music playlists (doubly linked for bidirectional navigation)
- Browser history (back/forward buttons)
- Undo/redo functionality
- Text buffer implementation (lines as linked list)

## 4.11 Historical Context

The linked list was invented by Allen Newell, Cliff Shaw, and Herbert A. Simon at RAND Corporation in 1956, as part of the development of the Information Processing Language (IPL), the first AI programming language.

John McCarthy made linked lists the fundamental data structure of LISP (1958) and introduced the names "car" and "cdr" (contents of the address part of register, contents of the decrement part of register) for the two fields of a list cell.

The doubly linked list emerged later as programmers recognized the need for bidirectional traversal.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**4.1 ★ Trace the core operations.** Using the singly linked list functions from Section 4.2, what does the list look like after each line? For each `delete_node` call, say which branch of the function does the work.

```c
Node *head = NULL;
insert_head(&head, 3);
insert_head(&head, 7);
insert_head(&head, 1);
insert_after(head->next, 5);
delete_node(&head, 1);
delete_node(&head, 3);
delete_node(&head, 9);
```

<details>
<summary>Solution</summary>

| Line | List afterwards |
|------|-----------------|
| `insert_head(&head, 3)` | 3 → NULL |
| `insert_head(&head, 7)` | 7 → 3 → NULL |
| `insert_head(&head, 1)` | 1 → 7 → 3 → NULL |
| `insert_after(head->next, 5)` | 1 → 7 → 5 → 3 → NULL |
| `delete_node(&head, 1)` | 7 → 5 → 3 → NULL |
| `delete_node(&head, 3)` | 7 → 5 → NULL |
| `delete_node(&head, 9)` | 7 → 5 → NULL |

- `insert_after(head->next, 5)`: `head->next` is the node holding 7, so 5 goes between 7 and 3.
- `delete_node(&head, 1)`: the key is in the head node, so the first `if` handles it by moving `*head_ref` to the second node. This is why the function takes `Node **`: it has to be able to change the caller's `head`.
- `delete_node(&head, 3)`: the `while` loop walks with `prev` one step behind `temp` (7, then 5) until `temp` reaches 3, then `prev->next = temp->next` unlinks it. `prev` is the 5 node, whose `next` becomes NULL.
- `delete_node(&head, 9)`: the loop runs off the end, `temp` is NULL, and the `if (temp == NULL) return;` line leaves the list unchanged.

</details>

**4.2 ★ The tail pointer doesn't help deletion.** The table in Section 4.8 lists "Insert at Tail" as O(1) for a singly linked list with a tail pointer, but "Delete at Tail" as O(n). Explain why the tail pointer helps one and not the other, and what a doubly linked list changes.

<details>
<summary>Solution</summary>

Inserting at the tail only touches the old tail node: set `tail->next = new_node`, then `tail = new_node`. The tail pointer gives direct access to that node, so it is O(1).

Deleting the tail requires changing the node *before* it: its `next` must become NULL, and `tail` must move to it. A singly linked node has no pointer to its predecessor, so the only way to find it is to walk from the head: O(n). Keeping a pointer to the second-to-last node doesn't fix this either, because after one deletion you need the third-to-last, and so on.

A doubly linked list stores `prev` in every node, so the new tail is `tail->prev`, found in O(1). That one extra pointer per node is the price of O(1) deletion at the tail, and of O(1) deletion of any node you hold a pointer to (Section 4.3). This is why queues (insert at one end, remove at the other) work fine on a singly linked list with a tail pointer, but deques need a doubly linked list or an array.

</details>

**4.3 ★★ Find the bug.** This function is meant to reverse a singly linked list in place and return the new head. On the list 1 → 2 → 3 → 4 it returns a list containing only 1. Why? Fix it.

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def reverse(head):
    prev = None
    cur = head
    while cur:
        cur.next = prev
        prev = cur
        cur = cur.next
    return prev
```

<details>
<summary>Hint</summary>

Trace the first iteration and write down what `cur.next` holds at the moment `cur = cur.next` runs.

</details>

<details>
<summary>Solution</summary>

First iteration: `cur` is node 1. `cur.next = prev` sets node 1's `next` to None, which destroys the only reference to node 2. Then `prev = cur` (node 1), and `cur = cur.next` reads the pointer that was just overwritten: `cur` becomes None. The loop ends and the function returns node 1, whose `next` is None. Nodes 2, 3 and 4 are lost (in C, leaked).

The fix is to save the rest of the list before rewiring the pointer:

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def reverse(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next      # save the rest of the list first
        cur.next = prev     # reverse this node's pointer
        prev = cur
        cur = nxt
    return prev


def to_list(node):
    out = []
    while node:
        out.append(node.data)
        node = node.next
    return out


head = Node(1, Node(2, Node(3, Node(4))))
assert to_list(reverse(head)) == [4, 3, 2, 1]
assert reverse(None) is None
assert to_list(reverse(Node(1))) == [1]
```

The invariant: at the top of each iteration, `prev` is the head of the already-reversed prefix and `cur` is the head of the untouched suffix. Overwriting `cur.next` before saving it breaks the link to the suffix. The function is O(n) time and O(1) extra space.

</details>

**4.4 ★★ XOR list by hand.** Four nodes A, B, C, D form an XOR linked list (Section 4.6), in that order, at addresses A = 0x10, B = 0x20, C = 0x30, D = 0x40. NULL is 0.

(a) Compute `npx` for every node.

(b) Traverse the list starting from D with `prev = NULL`, using the traversal loop from Section 4.6. Show each step.

(c) What do you need, at minimum, to start a traversal in the middle of the list, say at C?

<details>
<summary>Solution</summary>

**(a)** `npx` = address of previous XOR address of next.

| Node | prev | next | npx |
|------|------|------|-----|
| A | 0x00 | 0x20 | 0x20 |
| B | 0x10 | 0x30 | 0x20 |
| C | 0x20 | 0x40 | 0x60 |
| D | 0x30 | 0x00 | 0x30 |

(A and B happen to have the same `npx`. That's fine; `npx` only means something together with a neighbour's address.)

**(b)** Each step computes `next = prev ^ current->npx`.

| current | prev | next = prev ^ npx | visit |
|---------|------|-------------------|-------|
| D (0x40) | 0x00 | 0x00 ^ 0x30 = 0x30 (C) | D |
| C (0x30) | 0x40 | 0x40 ^ 0x60 = 0x20 (B) | C |
| B (0x20) | 0x30 | 0x30 ^ 0x20 = 0x10 (A) | B |
| A (0x10) | 0x20 | 0x20 ^ 0x20 = 0x00 (NULL) | A |

Output: D C B A. The same loop walks backwards when started from the tail, so an XOR list *can* be traversed in both directions; what it needs is the address of one end and the starting neighbour (NULL at either end).

**(c)** The address of C alone is useless: `npx` = 0x60 could be any pair of neighbours whose addresses XOR to 0x60. You need the addresses of two adjacent nodes, such as C and B (then `next = 0x20 ^ 0x60 = 0x40`, D) or C and D (then `next = 0x40 ^ 0x60 = 0x20`, B). For the same reason you can't delete a node given only a pointer to it, which takes away one of the doubly linked list's main advantages from Section 4.3.

</details>

**4.5 ★★ One sentinel, no special cases.** The doubly linked `delete_node` in Section 4.3 needs two `if` tests, and `insert_before` needs one, all for the head and tail cases. Implement a doubly linked list in Python with a single sentinel node that is both the "before head" and "after tail" node (the list is circular through the sentinel). Write `push_front`, `push_back`, `insert_before(node, data)` and `delete(node)` without any `if` statements.

<details>
<summary>Hint</summary>

An empty list is a sentinel whose `prev` and `next` both point to itself. Then every real node always has a real `prev` and `next` object, even when that object is the sentinel.

</details>

<details>
<summary>Solution</summary>

```python
class DNode:
    def __init__(self, data=None):
        self.data = data
        self.prev = self
        self.next = self


class DList:
    def __init__(self):
        self.sentinel = DNode()   # sentinel.next is the head, sentinel.prev the tail

    def insert_before(self, node, data):
        new = DNode(data)
        new.prev, new.next = node.prev, node
        node.prev.next = new
        node.prev = new
        return new

    def push_front(self, data):
        return self.insert_before(self.sentinel.next, data)

    def push_back(self, data):
        return self.insert_before(self.sentinel, data)

    def delete(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def __iter__(self):
        cur = self.sentinel.next
        while cur is not self.sentinel:
            yield cur.data
            cur = cur.next


lst = DList()
b = lst.push_back("b")
lst.push_front("a")
d = lst.push_back("d")
lst.insert_before(d, "c")
assert list(lst) == ["a", "b", "c", "d"]
lst.delete(b)
lst.delete(d)                      # deleting the tail: no special case
assert list(lst) == ["a", "c"]
lst.delete(lst.sentinel.next)      # deleting the head: no special case
lst.delete(lst.sentinel.next)      # list is now empty
assert list(lst) == [] and lst.sentinel.next is lst.sentinel
```

The branches disappear because the conditions they tested ("is `prev` NULL?", "is `next` NULL?") can no longer be true: the head's `prev` and the tail's `next` are the sentinel. The cost is one extra node per list, and iteration must stop at the sentinel instead of at NULL. Fewer branches means fewer places for the head/tail bugs that dominate linked list code; this is the "Both" pattern from Section 4.5 with the two sentinels merged into one, and it is how the Linux kernel's `list_head` works.

</details>

**4.6 ★★★ Unrolled list insertion.** Implement `insert(i, x)` for an unrolled linked list (Section 4.7) whose nodes hold at most B = 4 elements. When the target node is full, split it into two nodes of B/2 elements each, then insert. Then analyse: with n elements and node capacity B, what does one insert cost, and what B minimises it?

<details>
<summary>Hint</summary>

Walk node by node, subtracting each node's count from i, until i falls inside (or at the end of) the current node. After a split, decide which half the insertion position belongs to.

</details>

<details>
<summary>Solution</summary>

```python
import random

B = 4  # node capacity


class UNode:
    def __init__(self, items=None):
        self.items = items if items is not None else []   # at most B elements
        self.next = None


class UnrolledList:
    def __init__(self):
        self.head = UNode()
        self.n = 0

    def insert(self, i, x):
        """Insert x so that it ends up at position i (0 <= i <= n)."""
        if not 0 <= i <= self.n:
            raise IndexError(i)
        node = self.head
        while i > len(node.items) and node.next is not None:   # skip whole nodes
            i -= len(node.items)
            node = node.next
        if len(node.items) == B:                                # full: split in half
            half = B // 2
            right = UNode(node.items[half:])
            node.items = node.items[:half]
            right.next = node.next
            node.next = right
            if i > half:
                node, i = right, i - half
        node.items.insert(i, x)                                 # shifts at most B - 1
        self.n += 1

    def __iter__(self):
        node = self.head
        while node is not None:
            yield from node.items
            node = node.next


random.seed(7)
for trial in range(200):
    u, ref = UnrolledList(), []
    for k in range(random.randint(0, 60)):
        i = random.randint(0, len(ref))
        u.insert(i, k)
        ref.insert(i, k)
        assert list(u) == ref
```

**Cost.** A split always produces two nodes with B/2 elements, and nodes only grow between splits, so every node except possibly the first holds at least B/2 elements. There are therefore at most about 2n/B nodes. One insert costs:

- O(n/B) to walk to the right node (one step per node, not per element),
- O(B) to shift elements within the node (plus O(B) for a split, which copies half a node).

Total O(n/B + B). This is minimised when n/B = B, i.e. B ≈ √n, giving O(√n) per insert, against O(n) for both a plain array (shifting) and a plain linked list (walking). In practice B is chosen from the hardware instead, so that a node fills one or a few cache lines: the walk then touches n/B cache lines instead of n, which is where the "better cache locality" in Section 4.7 comes from. Pointer overhead also drops from one pointer per element to one pointer per B/2 or more elements.

</details>

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md). The contiguous alternative, and when it wins
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md). Why lock-free versions of these structures are hard
